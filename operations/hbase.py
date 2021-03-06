import ranger
from fabric.connection import Connection
from invoke import task

user = 'root'


@task(help={'namespace': 'HBase namespace to be created',
            'username': 'User owner of the namespace'})
def new(c, namespace, username):
    """
    Creates a new HBase namespace and gives ownership to user.
    """
    master_connection = Connection(c.config.master_host, user, config=c.config)
    create_hbase_namespace_hbase(master_connection, namespace)
    ranger.create_ranger_policy(
            c,
            ['{}.*'.format(namespace)],
            username,
            'hbase_{}'.format(namespace),
            'Hbase policy for namespace {}'.format(namespace),
            'table',
            'hbase')


def create_hbase_namespace_hbase(c, namespace_name):
    c.run('kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
        c.config.hbase_principal))
    c.run('echo "create_namespace \'{}\'" | hbase shell'.format(
        namespace_name))


@task(help={'namespace': 'HBase namespace to be deleted'})
def delete(c, namespace):
    """
    Deletes a HBase namespace.
    """
    master_connection = Connection(c.config.master_host, user, config=c.config)
    delete_hbase_namespace(master_connection, namespace)


def delete_hbase_namespace(c, namespace):
    c.run(
        'kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
            c.config.hbase_principal))
    c.run('echo "drop_namespace \'{}\'" | hbase shell'.format(
        namespace))
