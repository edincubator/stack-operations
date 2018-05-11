Operating the Big Data Stack
============================

.. note::

  This documentation is only for EDI Big Data Stack administrators. If you are
  a user, check :ref:`basicconcepts`.


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
  Available commands:

    create_hbase_namespace
    create_hive_database
    create_user
    delete_hbase_namespace
    delete_hive_database
    delete_user
  $

.. todo::

  Update according to the development of new tasks.

You can execute a task as:

.. code-block:: console

  $ fab create_user:username=newuser,email=newuser@company.org


Available tasks
---------------

create_user(username, email)
............................

This task creates a new user named `username` in EDI Big Data Stack, plus its
HDFS home directory and a Ranger policy for managing it. After its creation,
an email is sent to provided `email` indicating her Kerberos principal
and password.


delete_user(username)
.....................

Deletes a username from the system. Maintains her home directory at HDFS.


create_hive_database(database_name, username)
.............................................

Creates Hive database `database_name` and gives permissions to `username`.


delete_hive_database(database_name)
...................................

Deletes Hive database `database_name`.


create_hbase_namespace(namespace_name, username)
................................................

Creates HBase namespace `namespace_name` and gives permissions to `username`.


delete_hbase_namespace(namespace_name)
......................................

Deletes HBase namespace `namespace_name`
