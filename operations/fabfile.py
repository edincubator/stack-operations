import hbase
import hive
import kafka
import nifi
import user
from invoke import Collection

namespace = Collection(user, hive, hbase, kafka, nifi)
