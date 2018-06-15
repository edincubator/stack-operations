import hbase
import hive
import kafka
import user
from invoke import Collection

namespace = Collection(user, hive, hbase, kafka)
