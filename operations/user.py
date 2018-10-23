import json
import os
import smtplib
import uuid
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import hdfs
import invoke
import kerberos
import ldap
import ranger
import unix
import vpn
from fabric.connection import Connection

user = 'root'

# ldap_connection = Connection(settings.ldap_host, user)
# kerberos_connection = Connection(settings.kerberos_host, user)
# ranger_connection = Connection(settings.ranger_host, user)
# master_connection = Connection(settings.master_host, user)


@invoke.task(help={'username': 'Username of the user to be created',
                   'mail': 'Mail address for sending credentials',
                   'group': 'The group user belongs to',
                   'quota': 'HDFS Space quota for user'})
def new(c, username, mail, group=None, quota=''):
    """
    Creates a new user in the system.
    """
    password = os.urandom(6).encode('hex')

    for host in c.config.hosts:
        connection = Connection(host, user)
        unix.create_unix_user(connection, username)

    vpn_connection = Connection(c.config.vpn_host, user, config=c.config)
    ovpn_config = vpn.create_user(vpn_connection, username)

    ldap_connection = Connection(c.config.ldap_host, user, config=c.config)
    ldap.create_ldap_user(ldap_connection, username, password)
    if group is not None:
        ldap.add_user_to_ldap_group(ldap_connection, username, group)

    kerberos_connection = Connection(c.config.kerberos_host, user,
                                     config=c.config)
    kerberos.create_kerberos_user(kerberos_connection, username, password)

    folder_uuid = uuid.uuid1()
    file_uuid = uuid.uuid1()
    for nifi_host in c.config.nifi_servers:
        nifi_connection = Connection(nifi_host, user, config=c.config)
        kerberos.create_nifi_keytab(
            nifi_connection, username, folder_uuid, file_uuid)

    ranger_connection = Connection(c.config.ranger_host, user, config=c.config)
    ranger.update_ranger_usersync(ranger_connection)

    master_connection = Connection(c.config.master_host, user, config=c.config)
    hdfs.create_hdfs_home(master_connection, username)
    if not '':
        hdfs.set_space_quota(master_connection, username, quota)
    ranger.create_ranger_policy(
        c,
        ['/user/{}'.format(username)],
        username,
        'hdfs_home_{}'.format(username),
        'HDFS home directory for user {}'.format(username),
        'path',
        'hadoop'
        )
    ranger.update_nifi_flow_ranger_policy(c, username)

    sync_ambari_users(c)
    send_password_mail(
        c, username, password, mail, folder_uuid, file_uuid, ovpn_config)


@invoke.task(help={'username': 'Username of the user to be deleted',
                   'delete_home': 'Set for deleting user home directory'})
def delete(c, username, delete_home=False):
    """
    Deletes a user from the system.
    """
    ldap_connection = Connection(c.config.ldap_host, user, config=c.config)
    ldap.delete_ldap_user(ldap_connection, username)

    # Fabric can't detect Docker prompt, so we have to do this manually
    # vpn_connection = Connection(c.config.vpn_host, user, config=c.config)
    # vpn.delete_user(vpn_connection, username)

    for host in c.config.hosts:
        connection = Connection(host, user)
        unix.delete_unix_user(connection, username)
    if delete_home:
        master_connection = Connection(c.config.master_host, user,
                                       config=c.config)
        hdfs.delete_hdfs_home(master_connection, username)

    ranger_connection = Connection(c.config.ranger_host, user, config=c.config)
    ranger.update_ranger_usersync(ranger_connection)
    sync_ambari_users(c)


def sync_ambari_users(c):
    content = [
        {"Event":
            {"specs":
                [{"principal_type": "users", "sync_type": "all"},
                 {"principal_type": "groups", "sync_type": "all"}]
             }
         }]

    invoke.run(
        "curl -u {ambari_user}:{ambari_password} -H 'X-Requested-By: ambari'"
        " -X POST -d '{content}' {ambari_url}/api/v1/ldap_sync_events".format(
                ambari_user=c.config.ambari_user,
                ambari_password=c.config.ambari_password,
                content=json.dumps(content),
                ambari_url=c.config.ambari_url), pty=True)


def send_password_mail(c, username, password, mail, folder_uuid, file_uuid,
                       ovpn_config):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=c.config.kerberos_realm)
    msg = MIMEMultipart()
    text = '''Welcome to EDI Big Data Stack!\n\n
Those are your credentials for accesing to the system:\n\n
LDAP username: {username}\n
Kerberos Principal: {principal}\n
Password: {password}\n
NiFi keytab: {keytab}\n\n
Please, check out the documentation at https://docs.edincubator.eu'''.format(
        username=username,
        principal=principal,
        password=password,
        keytab='{folder_uuid}/{file_uuid}.keytab'.format(
            folder_uuid=folder_uuid,
            file_uuid=file_uuid
        ))

    msg['Subject'] = "[European Data Incubator] Big Data Stack Credentials"
    msg['From'] = "EDI - European Data Incubator <{}>".format(
        c.config.mail_from)
    msg['To'] = mail

    msg.attach(MIMEText(text))

    part = MIMEApplication(ovpn_config, Name='edi.ovpn')
    part['Content-Disposition'] = 'attachment; filename="edi.ovpn"'
    msg.attach(part)

    server = smtplib.SMTP(c.config.mail_host, c.config.mail_port)
    if c.config.mail_user is not None:
        server.login(c.config.mail_user, c.config.mail_password)
    server.sendmail(c.config.mail_from, [mail], msg.as_string())
    server.quit()
