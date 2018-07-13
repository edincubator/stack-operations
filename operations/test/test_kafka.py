from fabric.connection import Connection
from mockito import ANY, captor, unstub, verify, when
from operations import kafka, ranger


class TestKafka(object):
    def test_new(self):
        username = 'username'
        topic = 'topic'
        partitions = 1
        replication_factor = 2

        c = Connection('root')
        c.config.master_host = 'master.host'

        master_connection = captor(ANY(Connection))

        when(kafka).new_kafka_topic(
            master_connection, username, topic, partitions, replication_factor)

        kafka.new(c, username, topic, partitions, replication_factor)

        assert master_connection.value.config == c.config
        assert master_connection.value.host == c.config.master_host

        verify(kafka).new_kafka_topic(
            master_connection, username, topic, partitions, replication_factor)

        unstub()

    def test_new_kafka_topic(self):
        username = 'username'
        topic = 'topic'
        partitions = 1
        replication_factor = 2

        c = Connection('root')
        c.config.hdfs_principal = 'hdfs@EXAMPLE.ORG'
        c.config.kafka_client_dir = '/foo/bar'
        c.config.zookeeper_servers = ['host1', 'host2', 'host3']

        when(c).run(
            'kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
                c.config.hdfs_principal))

        when(c).run(
            '{client_dir}/bin/kafka-topics.sh --create --zookeeper '
            '{zookeeper_servers} --topic {topic} --partitions {partitions} '
            '--replication-factor {replication_factor}'.format(
                client_dir=c.config.kafka_client_dir,
                zookeeper_servers=' '.join(c.config.zookeeper_servers),
                topic=topic,
                partitions=partitions,
                replication_factor=replication_factor
            )
        )

        when(ranger).create_ranger_policy(
            c,
            [topic],
            username,
            'kafka_{}'.format(topic),
            'kafka policy for topic {}'.format(topic),
            'topic',
            'kafka'
        )

        kafka.new_kafka_topic(
            c, username, topic, partitions, replication_factor)

        verify(c).run(
            'kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
                c.config.hdfs_principal))

        verify(c).run(
            '{client_dir}/bin/kafka-topics.sh --create --zookeeper '
            '{zookeeper_servers} --topic {topic} --partitions {partitions} '
            '--replication-factor {replication_factor}'.format(
                client_dir=c.config.kafka_client_dir,
                zookeeper_servers=' '.join(c.config.zookeeper_servers),
                topic=topic,
                partitions=partitions,
                replication_factor=replication_factor
            )
        )

        verify(ranger).create_ranger_policy(
            c,
            [topic],
            username,
            'kafka_{}'.format(topic),
            'kafka policy for topic {}'.format(topic),
            'topic',
            'kafka'
        )

        unstub()
