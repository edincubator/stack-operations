from fabric.connection import Connection
from mockito import ANY, unstub, verify, when, mock
from operations import ldap
from invoke.runners import Result


class TestLdap(object):
    def test_create_ldap_user(self):
        username = 'username'
        password = 'password'
        c = Connection('root')
        c.config.ldap_manager_dn = 'cn=manager'
        c.config.ldap_manager_password = 'managerpassword'
        c.config.ldap_group_search_base = 'ou=Group,cn=example,cn=org'
        c.config.ldap_user_search_base = 'ou=People,cn=example,cn=org'

        mocked_result = mock(Result)
        mocked_result.stdout = 'mocked_id'

        when(c).run('id -u {}'.format(username)).thenReturn(mocked_result)
        when(c).put(ANY, '/tmp/user.ldif')
        when(c).run(
            'ldapadd -cxD {manager_dn} -w {manager_password} '
            '-f /tmp/user.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password)
            )

        ldap.create_ldap_user(c, username, password)

        verify(c, times=2).run('id -u {}'.format(username))
        verify(c).put(ANY, '/tmp/user.ldif')
        verify(c).run(
            'ldapadd -cxD {manager_dn} -w {manager_password} '
            '-f /tmp/user.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password)
            )

        unstub()
