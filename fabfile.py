import base64
import hashlib
import json
import os
import smtplib
import StringIO
from email.mime.text import MIMEText
from string import Template

import requests

import regex
import settings
from fabric.api import env, execute, local, put, run
from fabric.decorators import roles, task

env.user = 'root'
env.roledefs = {
    'hosts': settings.hosts,
    'kerberos': settings.kerberos_host,
    'ldap': settings.ldap_host,
    'master': settings.master_host,
    'ranger': settings.ranger_host
}


@task
def create_user(username, mail, group=None):
    password = os.urandom(6).encode('hex')

    execute(create_unix_user, username)
    execute(create_ldap_user, username, password)

    if group is not None:
        execute(add_user_to_ldap_group, username, group)

    execute(create_kerberos_user, username, password)

    execute(update_ranger_usersync)

    execute(create_hdfs_home, username)
    execute(create_ranger_policy,
            '/user/{}'.format(username),
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop'
            )
    execute(update_nifi_flow_ranger_policy, username)

    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)

    execute(sync_ambari_users)
    execute(send_password_mail, username, principal, password, mail)


@roles('hosts')
def create_unix_user(username):
    run('adduser {}'.format(username))
    run('usermod -s /sbin/nologin {}'.format(username))


@roles('ldap')
def create_ldap_user(username, password):
    uid = run('id -u {}'.format(username))
    gid = run('id -u {}'.format(username))

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

    put(output, '/tmp/user.ldif')

    run('ldapadd -cxD {manager_dn} -w {manager_password} '
        '-f /tmp/user.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


@roles('ldap')
def add_user_to_ldap_group(username, group):
    args = {'group': group,
            'group_search_base': settings.ldap_group_search_base,
            'username': username,
            'user_search_base': settings.ldap_user_search_base}

    filein = open('ldap_template/group.ldif')
    template = Template(filein.read())
    group_ldif = template.substitute(args)

    output = StringIO.StringIO()
    output.write(group_ldif)

    put(output, '/tmp/group.ldif')

    run('ldapmodify -xcD {manager_dn} -w {manager_password} '
        '-f /tmp/group.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


def sync_ambari_users():
    content = [
        {"Event":
            {"specs":
                [{"principal_type": "users", "sync_type": "all"},
                 {"principal_type": "groups", "sync_type": "all"}]
             }
         }]

    local("curl -u admin -H 'X-Requested-By: ambari' -X POST -d "
          "'{content}' {ambari_url}/api/v1/ldap_sync_events".format(
            content=json.dumps(content),
            ambari_url=settings.ambari_url))


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


@roles('ranger')
def update_ranger_usersync():
    run('/usr/jdk64/jdk1.8.0_112/bin/java -Dlogdir=/var/log/ranger/usersync '
        '-cp "/usr/hdp/current/ranger-usersync/dist/'
        'unixusersync-0.7.0.2.6.5.0-292.jar:/usr/hdp/current/ranger-usersync'
        '/dist/ranger-usersync-1.0-SNAPSHOT.jar:/usr/hdp/current/'
        'ranger-usersync/lib/*:/etc/ranger/usersync/conf" '
        'org.apache.ranger.usergroupsync.UserGroupSyncTrigger')


@roles('kerberos')
def create_kerberos_user(username, password):
    run('kadmin -p {admin_principal} addprinc -x '
        'dn="uid={username},{user_search_base}" -pw {password} '
        '{username}'.format(username=username,
                            user_search_base=settings.ldap_user_search_base,
                            password=password,
                            admin_principal=settings.kerberos_admin_principal)
        )


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


@roles('master')
def create_hdfs_home(username):
    run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        settings.hdfs_principal))
    run('hdfs dfs -mkdir /user/{}'.format(username))


@task
def delete_user(username):
    execute(delete_ldap_user, username)
    execute(delete_unix_user, username)


@roles('hosts')
def delete_unix_user(username):
    run('userdel {}'.format(username))


@roles('ldap')
def delete_ldap_user(username):
    output = run('ldapsearch -D "{manager_dn}" -w {manager_password} '
                 '-b "{user_search_base}" "uid={username}" "memberOf"'.format(
                    manager_dn=settings.ldap_manager_dn,
                    manager_password=settings.ldap_manager_password,
                    user_search_base=settings.ldap_user_search_base,
                    username=username
                 ))
    result = regex.search(r'memberOf: ([\w=,]+)', output)
    if result is not None:
        if len(result.groups()) > 0:
            group = result.groups()[0]

            run('ldapdelete -xcD {manager_dn} -w {manager_password} '
                '"{group}"'.format(
                    manager_dn=settings.ldap_manager_dn,
                    manager_password=settings.ldap_manager_password,
                    group=group
                ))

    run('ldapdelete -xcD {manager_dn} -w {manager_password} '
        '"uid={username},{user_search_base}"'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password,
            username=username,
            user_search_base=settings.ldap_user_search_base
        ))


@task
def create_hive_database(database_name, username):
    execute(create_hive_database_beeline, database_name)
    execute(create_ranger_policy,
            database_name,
            username,
            'hive_{}'.format(database_name),
            'HIVE database {}'.format(database_name),
            'database',
            'hive'
            )
    execute(create_ranger_policy,
            '/apps/hive/warehouse/{database}.db'.format(
                database=database_name),
            username,
            'hdfs_hive_{database}'.format(database=database_name),
            'HDFS directory for HIVE database {database}'.format(
                database=database_name),
            'path',
            'hadoop'
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


def update_nifi_flow_ranger_policy(username):
    response = requests.get(
        '{ranger_url}/service/public/v2/api/policy/{policy_id}'.format(
            ranger_url=settings.ranger_url,
            policy_id=settings.nifi_ranger_flow_policy_id),
        headers={'content-type': 'application/json'},
        auth=(settings.ranger_user, settings.ranger_password),
        verify=False)
    policy = response.json()
    policy['policyItems'][0]['users'].append(username)

    local("curl -X PUT {ranger_url}/service/public/v2/api/policy/{policy_id} "
          "-H 'authorization: Basic {auth_token}' "
          "-H 'content-type: application/json' "
          "-d '{content}' -k".format(
            ranger_url=settings.ranger_url,
            policy_id=settings.nifi_ranger_flow_policy_id,
            auth_token=base64.b64encode(
                '{ranger_user}:{ranger_password}'.format(
                    ranger_user=settings.ranger_user,
                    ranger_password=settings.ranger_password)),
            content=json.dumps(policy))
          )


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
          "-d '{content}' -k".format(
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


@task
@roles('master')
def delete_hbase_namespace(namespace_name):
    run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
        settings.hbase_principal))
    run('echo "drop_namespace \'{}\'" | hbase shell'.format(namespace_name))
