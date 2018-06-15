import ranger
import settings
from fabric.connection import Connection
from invoke import task

user = 'root'

master_connection = Connection(settings.master_host, user)


@task(help={'database': 'Name of the database to be created',
            'username': 'User owner of the database'})
def new(c, database, username):
    """
    Creates a new Hive database and gives ownership to a user.
    """
    create_hive_database_beeline(master_connection, database)
    ranger.create_ranger_policy(
            [database],
            username,
            'hive_{}'.format(database),
            'HIVE database {}'.format(database),
            'database',
            'hive'
            )
    ranger.create_ranger_policy(
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
    master_connection.run(
        'kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
            settings.hive_principal))
    master_connection.run('beeline -u "jdbc:hive2://{hive_url}/default;'
                          'principal={hive_principal};" '
                          '-e "DROP DATABASE {database_name}"'.format(
                            hive_url=settings.hive_url,
                            hive_principal=settings.hive_beeline_principal,
                            database_name=database))


def create_hive_database_beeline(c, database_name):
    c.run('kinit -kt /etc/security/keytabs/hive.service.keytab {}'.format(
            settings.hive_principal))
    c.run('beeline -u "jdbc:hive2://{hive_url}/default;'
          'principal={hive_principal};" '
          '-e "CREATE DATABASE {database_name}"'.format(
            hive_url=settings.hive_url,
            hive_principal=settings.hive_beeline_principal,
            database_name=database_name))
