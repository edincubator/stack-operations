from fabric.connection import Connection
from mockito import unstub, verify, when
from operations import hdfs


class TestHdfs(object):
    def test_create_hdfs_home(self):
        username = 'username'
        c = Connection('root')
        c.config.hdfs_principal = 'hdfs@EXAMPLE.COM'

        when(c).run(
            'kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
                c.config.hdfs_principal))
        when(c).run('hdfs dfs -mkdir /user/{}'.format(username))

        hdfs.create_hdfs_home(c, username)

        verify(c).run(
            'kinit -kt /etc/security/keytabs/hdfs.headless.keytab {}'.format(
                c.config.hdfs_principal))
        verify(c).run('hdfs dfs -mkdir /user/{}'.format(username))

        unstub()
