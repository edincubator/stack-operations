import settings


def create_hdfs_home(c, username):
    c.run('kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
        settings.hdfs_principal))
    c.run('hdfs dfs -mkdir /user/{}'.format(username))
