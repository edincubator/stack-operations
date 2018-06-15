import json
import os
import smtplib
from email.mime.text import MIMEText

import hdfs
import kerberos
import ldap
import ranger
import settings
import unix
from fabric.connection import Connection
from invoke import run, task

user = 'root'

ldap_connection = Connection(settings.ldap_host, user)
kerberos_connection = Connection(settings.kerberos_host, user)
ranger_connection = Connection(settings.ranger_host, user)
master_connection = Connection(settings.master_host, user)


@task(help={'username': 'Username of the user to be created',
            'mail': 'Mail address for sending credentials',
            'group': 'The group user belongs to'})
def new(c, username, mail, group=None):
    """
    Creates a new user in the system.
    """
    password = os.urandom(6).encode('hex')

    for host in settings.hosts:
        c = Connection(host, user)
        unix.create_unix_user(c, username)

    ldap.create_ldap_user(ldap_connection, username, password)

    if group is not None:
        ldap.add_user_to_ldap_group(ldap_connection, username, group)

    kerberos.create_kerberos_user(kerberos_connection, username, password)
    folder_uuid, file_uuid = kerberos.create_nifi_keytab(
        kerberos_connection, username)

    ranger.update_ranger_usersync(ranger_connection)

    hdfs.create_hdfs_home(master_connection, username)
    ranger.create_ranger_policy(
            '/user/{}'.format(username),
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop'
            )
    ranger.update_nifi_flow_ranger_policy(username)

    sync_ambari_users()
    send_password_mail(username, password, mail, folder_uuid, file_uuid)


def sync_ambari_users():
    content = [
        {"Event":
            {"specs":
                [{"principal_type": "users", "sync_type": "all"},
                 {"principal_type": "groups", "sync_type": "all"}]
             }
         }]

    run("curl -u admin -H 'X-Requested-By: ambari' -X POST -d "
        "'{content}' {ambari_url}/api/v1/ldap_sync_events".format(
            content=json.dumps(content),
            ambari_url=settings.ambari_url), pty=True)


def send_password_mail(username, password, mail, folder_uuid, file_uuid):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)
    msg = MIMEText('''Welcome to EDI Big Data Stack!\n\n
Those are your credentials for accesing to the system:\n\n
LDAP username: {username}\n
Kerberos Principal: {principal}\n
Password: {password}\n
NiFi keytab: {keytab}'''.format(
        username=username,
        principal=principal,
        password=password,
        keytab='{folder_uuid}/{file_uuid}.keytab'.format(
            folder_uuid=folder_uuid,
            file_uuid=file_uuid
        )))
    msg['Subject'] = "[European Data Incubator] Big Data Stack Credentials"
    msg['From'] = "EDI - European Data Incubator <{}>".format(
        settings.mail_from)
    msg['To'] = mail

    server = smtplib.SMTP(settings.mail_host, settings.mail_port)
    if settings.mail_user is not None:
        server.login(settings.mail_user, settings.mail_password)
    server.sendmail(settings.mail_from, [mail], msg.as_string())
    server.quit()
