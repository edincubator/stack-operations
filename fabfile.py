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
    run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        settings.hdfs_principal))
    run('hdfs dfs -mkdir /user/{}'.format(username))


def create_hdfs_default_policy(username):
    create_ranger_policy(
        '/user/{}'.format(username),
        username,
        'hdfs_home_{}'.format(username),
        'HDFS home directory for user {}'.format(username),
        'path',
        'hdfs'
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


@task
def create_hive_database(database_name, username):
    execute(create_hive_database_beeline, database_name)
    execute(create_hive_database_policy, database_name, username)
    execute(create_hive_database_hdfs_policy, database_name, username)


def create_hive_database_hdfs_policy(database_name, username):
    create_ranger_policy(
        '/apps/hive/warehouse/{database}.db'.format(database=database_name),
        username,
        'hdfs_hive_{database}'.format(database=database_name),
        'HDFS directory for HIVE database {database}'.format(
            database=database_name),
        'path',
        'hdfs'
    )


def create_hive_database_policy(database_name, username):
    create_ranger_policy(
        database_name,
        username,
        'hive_{}'.format(database_name),
        'HIVE database {}'.format(database_name),
        'database',
        'hive'
    )


@roles('master')
def create_hive_database_beeline(database_name):
    run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
        settings.hive_principal))
    run('beeline -u "jdbc:hive2://{hive_url}/default;'
        'principal={hive_principal};" '
        '-e "CREATE DATABASE {database_name}"'.format(
            hive_url=settings.hive_url,
            hive_principal=settings.hive_beeline_principal,
            database_name=database_name))


def create_ranger_policy(resource, username, policy_name, policy_description,
                         resource_type, service):
    template = json.load(open('ranger_templates/{}.json'.format(service), 'r'))
    template['service'] = '{cluster_name}_{service}'.format(
        cluster_name=settings.ranger_cluster_name, service=service)
    template['name'] = policy_name
    template['description'] = policy_description
    template['resources'][resource_type]['values'].append(resource)
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
@roles('master')
def delete_hive_database(database_name):
    run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
        settings.hive_principal))
    run('beeline -u "jdbc:hive2://{hive_url}/default;'
        'principal={hive_principal};" '
        '-e "DROP DATABASE {database_name}"'.format(
            hive_url=settings.hive_url,
            hive_principal=settings.hive_beeline_principal,
            database_name=database_name))


@task
def create_hbase_namespace(namespace_name, username):
    execute(create_hbase_namespace_hbase, namespace_name)
    execute(create_ranger_policy,
            '{}:*'.format(namespace_name),
            username,
            'hbase_{}'.format(namespace_name),
            'Hbase policy for namespace {}'.format(namespace_name),
            'table',
            'hbase')


@roles('master')
def create_hbase_namespace_hbase(namespace_name):
    run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
        settings.hbase_principal))
    run('echo "create_namespace \'{}\'" | hbase shell'.format(namespace_name))
