def create_hdfs_home(c, username):
    c.run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        c.config.hdfs_principal))
    c.run('hdfs dfs -mkdir /user/{}'.format(username))


def delete_hdfs_home(c, username):
    c.run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        c.config.hdfs_principal))
    c.run('hdfs dfs -rm -r /user/{}'.format(username))
