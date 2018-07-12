from fabric.connection import Connection
from mockito import ANY, captor, unstub, verify, when
from operations import hive, ranger


class TestHive(object):
    def test_new(self):
        database = 'db'
        username = 'username'

        c = Connection('root')
        c.config.master_host = 'master.host'

        hive_connection = captor(ANY(Connection))

        when(hive).create_hive_database_beeline(hive_connection, database)
        when(ranger).create_ranger_policy(
            c,
            [database],
            username,
            'hive_{}'.format(database),
            'HIVE database {}'.format(database),
            'database',
            'hive'
        )
        when(ranger).create_ranger_policy(
                c,
                ['/apps/hive/warehouse/{database}.db'.format(
                    database=database)],
                username,
                'hdfs_hive_{database}'.format(database=database),
                'HDFS directory for HIVE database {database}'.format(
                    database=database),
                'path',
                'hadoop'
                )

        hive.new(c, database, username)

        assert hive_connection.value.host == c.config.master_host

        verify(ranger).create_ranger_policy(
            c,
            [database],
            username,
            'hive_{}'.format(database),
            'HIVE database {}'.format(database),
            'database',
            'hive'
        )
        verify(ranger).create_ranger_policy(
                c,
                ['/apps/hive/warehouse/{database}.db'.format(
                    database=database)],
                username,
                'hdfs_hive_{database}'.format(database=database),
                'HDFS directory for HIVE database {database}'.format(
                    database=database),
                'path',
                'hadoop'
                )

        unstub()

    def test_delete(self):
        database = 'db'

        c = Connection('root')
        c.config.master_host = 'master.host'

        master_connection = captor(ANY(Connection))

        when(hive).delete_hive_database(master_connection, database)

        hive.delete(c, database)

        verify(hive).delete_hive_database(master_connection, database)

        assert master_connection.value.host == c.config.master_host
        unstub()

    def test_delete_hive_database(self):
        database = 'db'

        c = Connection('root')
        c.config.master_host = 'master.host'
        c.config.hive_principal = 'hive@EXAMPLE.COM'
        c.config.hive_url = 'http://hive.url'
        c.config.hive_beeline_principal = 'beeline@EXAMPLE.COM'

        when(c).run(
            'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
                c.config.hive_principal))
        when(c).run(
            'beeline -u "jdbc:hive2://{hive_url}/default;'
            'principal={hive_principal};" '
            '-e "DROP DATABASE {database_name}"'.format(
                hive_url=c.config.hive_url,
                hive_principal=c.config.hive_beeline_principal,
                database_name=database))

        hive.delete_hive_database(c, database)

        verify(c).run(
            'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
                c.config.hive_principal))
        verify(c).run(
            'beeline -u "jdbc:hive2://{hive_url}/default;'
            'principal={hive_principal};" '
            '-e "DROP DATABASE {database_name}"'.format(
                hive_url=c.config.hive_url,
                hive_principal=c.config.hive_beeline_principal,
                database_name=database))

        unstub()

    def test_create_hive_database_beeline(self):
        database = 'db'

        c = Connection('root')
        c.config.hive_principal = 'hive@EXAMPLE.COM'
        c.config.hive_url = 'http://hive.url'
        c.config.hive_beeline_principal = 'beeline@EXAMPLE.COM'

        when(c).run(
            'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
                c.config.hive_principal))
        when(c).run(
              'beeline -u "jdbc:hive2://{hive_url}/default;'
              'principal={hive_principal};" '
              '-e "CREATE DATABASE {database_name}"'.format(
                hive_url=c.config.hive_url,
                hive_principal=c.config.hive_beeline_principal,
                database_name=database))

        hive.create_hive_database_beeline(c, database)

        verify(c).run(
            'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
                c.config.hive_principal))
        verify(c).run(
              'beeline -u "jdbc:hive2://{hive_url}/default;'
              'principal={hive_principal};" '
              '-e "CREATE DATABASE {database_name}"'.format(
                hive_url=c.config.hive_url,
                hive_principal=c.config.hive_beeline_principal,
                database_name=database))

        unstub()
