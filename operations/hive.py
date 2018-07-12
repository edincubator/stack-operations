import ranger
from fabric.connection import Connection
from invoke import task

user = 'root'


@task(help={'database': 'Name of the database to be created',
            'username': 'User owner of the database'})
def new(c, database, username):
    """
    Creates a new Hive database and gives ownership to a user.
    """
    master_connection = Connection(c.config.master_host, user)
    create_hive_database_beeline(master_connection, database)
    ranger.create_ranger_policy(
            c,
            [database],
            username,
            'hive_{}'.format(database),
            'HIVE database {}'.format(database),
            'database',
            'hive'
            )
    ranger.create_ranger_policy(
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


@task(help={'database': 'Database to be created'})
def delete(c, database):
    """
    Deletes a Hive database.
    """
    master_connection = Connection(c.config.master_host, user)
    delete_hive_database(master_connection, database)


def delete_hive_database(c, database):
    c.run(
        'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
            c.config.hive_principal))
    c.run('beeline -u "jdbc:hive2://{hive_url}/default;'
          'principal={hive_principal};" '
          '-e "DROP DATABASE {database_name}"'.format(
            hive_url=c.config.hive_url,
            hive_principal=c.config.hive_beeline_principal,
            database_name=database))


def create_hive_database_beeline(c, database_name):
    c.run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
            c.config.hive_principal))
    c.run('beeline -u "jdbc:hive2://{hive_url}/default;'
          'principal={hive_principal};" '
          '-e "CREATE DATABASE {database_name}"'.format(
            hive_url=c.config.hive_url,
            hive_principal=c.config.hive_beeline_principal,
            database_name=database_name))
