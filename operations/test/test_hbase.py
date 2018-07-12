from fabric.connection import Connection
from mockito import ANY, unstub, verify, when
from mockito.matchers import captor
from operations import hbase, ranger


class TestHbase(object):
    def test_new(self):
        namespace = 'ns'
        username = 'username'

        c = Connection('root')
        c.config.master_host = 'master.host'

        hbase_connection = captor(ANY(Connection))

        when(hbase).create_hbase_namespace_hbase(hbase_connection, namespace)
        when(ranger).create_ranger_policy(
            c,
            ['{}.*'.format(namespace)],
            username,
            'hbase_{}'.format(namespace),
            'Hbase policy for namespace {}'.format(namespace),
            'table',
            'hbase'
        )

        hbase.new(c, namespace, username)

        assert hbase_connection.value.host == c.config.master_host

        verify(hbase).create_hbase_namespace_hbase(hbase_connection, namespace)
        verify(ranger).create_ranger_policy(
            c,
            ['{}.*'.format(namespace)],
            username,
            'hbase_{}'.format(namespace),
            'Hbase policy for namespace {}'.format(namespace),
            'table',
            'hbase'
        )

        unstub()

    def test_create_hbase_namespace_hbase(self):
        namespace = 'ns'
        c = Connection('root')
        c.config.hbase_principal = 'hbase@EXAMPLE.COM'

        when(c).run(
            'kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
                c.config.hbase_principal))

        when(c).run('echo "create_namespace \'{}\'" | hbase shell'.format(
            namespace))

        hbase.create_hbase_namespace_hbase(c, namespace)

        verify(c).run(
            'kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
                c.config.hbase_principal))
        verify(c).run('echo "create_namespace \'{}\'" | hbase shell'.format(
            namespace))

        unstub()

    def test_delete_hbase_namespace(self):
        namespace = 'ns'
        c = Connection('root')
        c.config.master_host = 'master.host'
        c.config.hbase_principal = 'hbase@EXAMPLE.COM'

        when(c).run(
            'kinit -kt /etc/security/keytabs/hbase.headless.keytab {}'.format(
                c.config.hbase_principal))
        when(c).run(
            'echo "drop_namespace \'{}\'" | hbase shell'.format(namespace))

        hbase.delete_hbase_namespace(c, namespace)

        unstub()

    def test_delete(self):
        namespace = 'ns'
        c = Connection('root')
        c.config.master_host = 'master.host'

        master_connection = captor(ANY(Connection))

        when(hbase).delete_hbase_namespace(master_connection, namespace)

        hbase.delete(c, namespace)

        verify(hbase).delete_hbase_namespace(master_connection, namespace)
        assert master_connection.value.host == c.config.master_host

        unstub()
