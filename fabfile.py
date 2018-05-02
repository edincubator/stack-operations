import base64
import json
import smtplib
import uuid
from email.mime.text import MIMEText

import settings
from fabric.api import env, execute, local, run
from fabric.decorators import roles, task

env.user = 'root'
env.roledefs = {
    'hosts': settings.hosts,
    'kerberos': settings.kerberos_host,
    'master': settings.master_host
}


@task
def create_user(username, mail):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)

    kpass = execute(create_kerberos_user,
                    ('{username}@{realm}'.format(
                        username=username,
                        realm=settings.kerberos_realm)))

    execute(create_unix_user, username)
    execute(create_hdfs_home, username)
    execute(create_hdfs_default_policy, username)
    execute(send_password_mail, username, principal,
            str(kpass.get(settings.kerberos_host[0])), mail)


@roles('hosts')
def create_unix_user(username):
    run('adduser {}'.format(username))
    run('usermod -s /sbin/nologin {}'.format(username))


@roles('kerberos')
def create_kerberos_user(principal, password=None):
    if password is None:
        password = uuid.uuid4()
    run('kadmin -p {admin_principal} addprinc -pw {password} +needchange '
        '{principal}'.format(
            admin_principal=settings.kerberos_admin_principal,
            password=password, principal=principal))
    return password


def send_password_mail(username, principal, password, mail):
    msg = MIMEText('''Welcome to EDI Big Data Stack!\n\n
Those are your Kerberos credentials for accesing to the system:\n\n
Principal: {principal}\n
Password: {password}'''.format(mail_from=settings.mail_from, to=mail,
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


@roles('master')
def create_hdfs_home(username):
    run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab hdfs-edi_test')
    run('hdfs dfs -mkdir /user/{}'.format(username))


def create_hdfs_default_policy(username):

    template = json.load(open('ranger_templates/hdfs.json', 'r'))
    template['service'] = settings.cluster_name
    template['name'] = 'hdfs_home_{}'.format(username)
    template['description'] = 'HDFS home directory for user {}'.format(
        username)
    template['resources']['path']['values'].append('/user/{}'.format(username))
    template['policyItems'][0]['users'].append(username)

    local("curl -X POST {ranger_url}/service/public/v2/api/policy "
          "-H 'authorization: Basic {auth_token}' "
          "-H 'content-type: application/json' "
          "-d '{content}'".format(
            ranger_url=settings.ranger_url,
            auth_token=base64.b64encode(
                '{ranger_user}:{ranger_password}'.format(
                    ranger_user=settings.ranger_user,
                    ranger_password=settings.ranger_password)),
            content=json.dumps(template))
          )


@task
def delete_user(username):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)
    execute(delete_kerberos_user, principal)
    execute(delete_unix_user, username)


@roles('hosts')
def delete_unix_user(username):
    run('userdel {}'.format(username))


@roles('kerberos')
def delete_kerberos_user(principal):
    run('kadmin -p {admin_principal} delete_principal {principal}'.format(
        principal=principal,
        admin_principal=settings.kerberos_admin_principal))
