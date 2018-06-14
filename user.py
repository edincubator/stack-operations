import hashlib
import json
import os
import smtplib
import StringIO
from email.mime.text import MIMEText
from string import Template

import ranger
import settings
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
        create_unix_user(c, username)

    create_ldap_user(ldap_connection, username, password)

    if group is not None:
        add_user_to_ldap_group(ldap_connection, username, group)

    create_kerberos_user(kerberos_connection, username, password)

    ranger.update_ranger_usersync(ranger_connection)

    create_hdfs_home(master_connection, username)
    ranger.create_ranger_policy(
            '/user/{}'.format(username),
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop'
            )
    ranger.update_nifi_flow_ranger_policy(username)

    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)

    sync_ambari_users()
    send_password_mail(username, principal, password, mail)


def create_unix_user(c, username):
    c.run('adduser {}'.format(username))
    c.run('usermod -s /sbin/nologin {}'.format(username))


def create_ldap_user(c, username, password):
    uid = c.run('id -u {}'.format(username)).stdout.strip()
    gid = c.run('id -u {}'.format(username)).stdout.strip()

    args = {'username': username,
            'group_search_base': settings.ldap_group_search_base,
            'gid': gid,
            'user_search_base': settings.ldap_user_search_base,
            'uid': uid,
            'password': make_secret(password)}

    filein = open('ldap_template/user.ldif')
    template = Template(filein.read())
    user_ldif = template.substitute(args)

    output = StringIO.StringIO()
    output.write(user_ldif)

    c.put(output, '/tmp/user.ldif')

    c.run('ldapadd -cxD {manager_dn} -w {manager_password} '
          '-f /tmp/user.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


def make_secret(password):
    """
    Encodes the given password as a base64 SSHA hash+salt buffer
    """
    salt = os.urandom(4)

    # hash the password and append the salt
    sha = hashlib.sha1(password)
    sha.update(salt)

    # create a base64 encoded string of the concatenated digest + salt
    digest_salt_b64 = '{}{}'.format(sha.digest(),
                                    salt).encode('base64').strip()

    return digest_salt_b64


def add_user_to_ldap_group(c, username, group):
    args = {'group': group,
            'group_search_base': settings.ldap_group_search_base,
            'username': username,
            'user_search_base': settings.ldap_user_search_base}

    filein = open('ldap_template/group.ldif')
    template = Template(filein.read())
    group_ldif = template.substitute(args)

    output = StringIO.StringIO()
    output.write(group_ldif)

    c.put(output, '/tmp/group.ldif')

    c.run('ldapmodify -xcD {manager_dn} -w {manager_password} '
          '-f /tmp/group.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


def create_kerberos_user(c, username, password):
    c.run('kadmin -p {admin_principal} addprinc -x '
          'dn="uid={username},{user_search_base}" -pw {password} '
          '{username}'.format(
            username=username,
            user_search_base=settings.ldap_user_search_base,
            password=password,
            admin_principal=settings.kerberos_admin_principal), pty=True
          )


def create_hdfs_home(c, username):
    c.run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        settings.hdfs_principal))
    c.run('hdfs dfs -mkdir /user/{}'.format(username))


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


def send_password_mail(username, principal, password, mail):
    msg = MIMEText('''Welcome to EDI Big Data Stack!\n\n
Those are your credentials for accesing to the system:\n\n
LDAP username: {username}\n
Kerberos Principal: {principal}\n
Password: {password}'''.format(username=username,
                               principal=principal,
                               password=password))
    msg['Subject'] = "[European Data Incubator] Big Data Stack Credentials"
    msg['From'] = "EDI - European Data Incubator <{}>".format(
        settings.mail_from)
    msg['To'] = mail

    server = smtplib.SMTP(settings.mail_host, settings.mail_port)
    if settings.mail_user is not None:
        server.login(settings.mail_user, settings.mail_password)
    server.sendmail(settings.mail_from, [mail], msg.as_string())
    server.quit()
