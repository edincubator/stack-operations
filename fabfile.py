import hbase
import hive
import user
from invoke import Collection

namespace = Collection(user, hive, hbase)


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
