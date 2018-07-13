from fabric.connection import Connection
from operations import unix
from mockito import unstub, verify, when


class TestUnix(object):
    def test_create_unix_user(self):
        username = 'username'
        c = Connection('root')

        when(c).run('adduser {}'.format(username))
        when(c).run('usermod -s /sbin/nologin {}'.format(username))

        unix.create_unix_user(c, username)

        verify(c).run('adduser {}'.format(username))
        verify(c).run('usermod -s /sbin/nologin {}'.format(username))

        unstub()

    def test_delete_unix_user(self):
        username = 'username'
        c = Connection('root')

        when(c).run('userdel {}'.format(username))

        unix.delete_unix_user(c, username)

        verify(c).run('userdel {}'.format(username))

        unstub()
