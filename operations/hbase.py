import ranger
import settings
from fabric.connection import Connection
from invoke import task

user = 'root'

master_connection = Connection(settings.master_host, user)


@task(help={'namespace': 'HBase namespace to be created',
            'username': 'User owner of the namespace'})
def new(c, namespace, username):
    """
    Creates a new HBase namespace and gives ownership to user.
    """
    create_hbase_namespace_hbase(master_connection, namespace)
    ranger.create_ranger_policy(
            ['{}.*'.format(namespace)],
            username,
            'hbase_{}'.format(namespace),
            'Hbase policy for namespace {}'.format(namespace),
            'table',
            'hbase')


def create_hbase_namespace_hbase(c, namespace_name):
    c.run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
        settings.hbase_principal))
    c.run('echo "create_namespace \'{}\'" | hbase shell'.format(
        namespace_name))


@task(help={'namespace': 'HBase namespace to be deleted'})
def delete(c, namespace):
    """
    Deletes a HBase namespace.
    """
    master_connection.run(
        'kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
            settings.hbase_principal))
    master_connection.run('echo "drop_namespace \'{}\'" | hbase shell'.format(
        namespace))
