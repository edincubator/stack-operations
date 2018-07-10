import ranger
from fabric.connection import Connection
from invoke import task

user = 'root'


@task(help={'username': 'User owner of the topic',
            'topic': 'Name of the topic to be created',
            'partitions': 'Number of partitions',
            'replication-factor': 'Replication factor'})
def new(c, username, topic, partitions=1, replication_factor=1):
    """
    Creates a new Kafka topic and gives ownership to user.
    """
    master_connection = Connection(c.config.master_host, user)
    master_connection.run(
        'kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
            c.config.hdfs_principal))

    master_connection.run(
        '{client_dir}/bin/kafka-topics.sh --create --zookeeper '
        '{zookeeper_servers} --topic {topic} --partitions {partitions} '
        '--replication-factor {replication_factor}'.format(
            client_dir=c.config.kafka_client_dir,
            zookeeper_servers=' '.join(c.config.zookeeper_servers),
            topic=topic,
            partitions=partitions,
            replication_factor=replication_factor
        ))

    ranger.create_ranger_policy(
            [topic],
            username,
            'kafka_{}'.format(topic),
            'kafka policy for topic {}'.format(topic),
            'topic',
            'kafka')
