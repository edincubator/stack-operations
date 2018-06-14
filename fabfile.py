import base64
import hashlib
import json
import os
import smtplib
import StringIO
from email.mime.text import MIMEText
from string import Template

import requests

from invoke import task, Collection
import user

import regex
import settings

namespace = Collection(user)

# env.user = 'root'
# env.roledefs = {
#     'hosts': settings.hosts,
#     'kerberos': settings.kerberos_host,
#     'ldap': settings.ldap_host,
#     'master': settings.master_host,
#     'ranger': settings.ranger_host
# }
#
#
#
# @task
# def delete_user(username):
#     execute(delete_ldap_user, username)
#     execute(delete_unix_user, username)
#     execute(sync_ambari_users)
#
#
# @roles('hosts')
# def delete_unix_user(username):
#     run('userdel {}'.format(username))
#
#
# @roles('ldap')
# def delete_ldap_user(username):
#     output = run('ldapsearch -D "{manager_dn}" -w {manager_password} '
#                  '-b "{user_search_base}" "uid={username}" "memberOf"'.format(
#                     manager_dn=settings.ldap_manager_dn,
#                     manager_password=settings.ldap_manager_password,
#                     user_search_base=settings.ldap_user_search_base,
#                     username=username
#                  ))
#     result = regex.search(r'memberOf: ([\w=,]+)', output)
#     if result is not None:
#         if len(result.groups()) > 0:
#             group = result.groups()[0]
#
#             args = {
#                 'group': group,
#                 'username': username,
#                 'user_search_base': settings.ldap_user_search_base
#             }
#
#             filein = open('ldap_template/delete_member.ldif')
#             template = Template(filein.read())
#             delete_member_ldif = template.substitute(args)
#
#             output = StringIO.StringIO()
#             output.write(delete_member_ldif)
#
#             put(output, '/tmp/delete_member.ldif')
#
#             run('ldapmodify -xcD "{manager_dn}" -w {manager_password} '
#                 '-f /tmp/delete_member.ldif'.format(
#                     manager_dn=settings.ldap_manager_dn,
#                     manager_password=settings.ldap_manager_password
#                 ))
#
#     run('ldapdelete -xcD {manager_dn} -w {manager_password} '
#         '"uid={username},{user_search_base}"'.format(
#             manager_dn=settings.ldap_manager_dn,
#             manager_password=settings.ldap_manager_password,
#             username=username,
#             user_search_base=settings.ldap_user_search_base
#             ))
#
#
# @task
# def create_hive_database(database_name, username):
#     execute(create_hive_database_beeline, database_name)
#     execute(create_ranger_policy,
#             database_name,
#             username,
#             'hive_{}'.format(database_name),
#             'HIVE database {}'.format(database_name),
#             'database',
#             'hive'
#             )
#     execute(create_ranger_policy,
#             '/apps/hive/warehouse/{database}.db'.format(
#                 database=database_name),
#             username,
#             'hdfs_hive_{database}'.format(database=database_name),
#             'HDFS directory for HIVE database {database}'.format(
#                 database=database_name),
#             'path',
#             'hadoop'
#             )
#
#
# @roles('master')
# def create_hive_database_beeline(database_name):
#     run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
#         settings.hive_principal))
#     run('beeline -u "jdbc:hive2://{hive_url}/default;'
#         'principal={hive_principal};" '
#         '-e "CREATE DATABASE {database_name}"'.format(
#             hive_url=settings.hive_url,
#             hive_principal=settings.hive_beeline_principal,
#             database_name=database_name))
#
#
#
#
#
#
#
#
# @task
# @roles('master')
# def delete_hive_database(database_name):
#     run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
#         settings.hive_principal))
#     run('beeline -u "jdbc:hive2://{hive_url}/default;'
#         'principal={hive_principal};" '
#         '-e "DROP DATABASE {database_name}"'.format(
#             hive_url=settings.hive_url,
#             hive_principal=settings.hive_beeline_principal,
#             database_name=database_name))
#
#
# @task
# def create_hbase_namespace(namespace_name, username):
#     execute(create_hbase_namespace_hbase, namespace_name)
#     execute(create_ranger_policy,
#             '{}:*'.format(namespace_name),
#             username,
#             'hbase_{}'.format(namespace_name),
#             'Hbase policy for namespace {}'.format(namespace_name),
#             'table',
#             'hbase')
#
#
# @roles('master')
# def create_hbase_namespace_hbase(namespace_name):
#     run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
#         settings.hbase_principal))
#     run('echo "create_namespace \'{}\'" | hbase shell'.format(namespace_name))
#
#
# @task
# @roles('master')
# def delete_hbase_namespace(namespace_name):
#     run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
#         settings.hbase_principal))
#     run('echo "drop_namespace \'{}\'" | hbase shell'.format(namespace_name))
#
#
# @task
# @roles('master')
# def create_kafka_topic(username, topic, partitions=1, replication_factor=1):
#     run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
#         settings.hdfs_principal))
#
#     run('{client_dir}/bin/kafka-topics.sh --create --zookeeper '
#         '{zookeeper_servers} --topic {topic} --partitions {partitions} '
#         '--replication-factor {replication_factor}'.format(
#             client_dir=settings.kafka_client_dir,
#             zookeeper_servers=' '.join(settings.zookeeper_servers),
#             topic=topic,
#             partitions=partitions,
#             replication_factor=replication_factor
#         ))
#
#     execute(create_ranger_policy,
#             topic,
#             username,
#             'kafka_{}'.format(topic),
#             'kafka policy for topic {}'.format(topic),
#             'topic',
#             'kafka')
