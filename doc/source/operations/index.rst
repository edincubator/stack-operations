Operating the Big Data Stack
============================

For operating the Big Data Stack, there is a `Fabric <http://www.fabfile.org/>`_
script available at https://github.com/edincubator/stack-operations. For using
this fabric script follow these steps:

.. code-block:: console

  $ git clone  https://github.com/edincubator/stack-operations
  $ cd stack-operations
  $ pip install -r requirements.txt

You can list available tasks executing `fab --list`:

.. code-block:: console

  $ fab --list
  Available tasks:

    hbase.delete   Deletes a HBase namespace.
    hbase.new      Creates a new HBase namespace and gives ownership to user.
    hive.delete    Deletes a Hive database.
    hive.new       Creates a new Hive database and gives ownership to a user.
    kafka.new      Creates a new Kafka topic and gives ownership to user.
    user.delete    Deletes a user from the system.
    user.new       Creates a new user in the system.

  $

.. todo::

  Update according to the development of new tasks.

You can get more details about a task using `fab --help` command:

.. code-block:: console

  $ fab --help user.new
  Usage: fab [--core-opts] user.new [--options] [other tasks here ...]

  Docstring:
    Creates a new user in the system.

  Options:
    -g STRING, --group=STRING      The group user belongs to
    -m STRING, --mail=STRING       Mail address for sending credentials
    -u STRING, --username=STRING   Username of the user to be created

  $


You can execute a task as:

.. code-block:: console

  $ fab user.new -u newuser -m newuser@company.org -g mygroup


Available tasks
---------------

User
....

.. automodule:: operations.user
   :members:

Hive
....

.. automodule:: operations.hive
   :members:

HBase
.....

.. automodule:: operations.hbase
   :members:

Kafka
.....

.. automodule:: operations.kafka
   :members:
