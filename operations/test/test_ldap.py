from fabric.connection import Connection
from invoke.runners import Result
from mockito import ANY, mock, unstub, verify, when
from operations import ldap


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

    def test_add_user_to_ldap_group(self):
        username = 'username'
        group = 'group'

        c = Connection('root')
        c.config.ldap_manager_dn = 'cn=manager'
        c.config.ldap_manager_password = 'managerpassword'
        c.config.ldap_group_search_base = 'ou=Group,cn=example,cn=org'
        c.config.ldap_user_search_base = 'ou=People,cn=example,cn=org'

        when(c).put(ANY, '/tmp/group.ldif')
        when(c).run(
            'ldapmodify -xcD {manager_dn} -w {manager_password} '
            '-f /tmp/group.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password)
        )

        ldap.add_user_to_ldap_group(c, username, group)

        verify(c).put(ANY, '/tmp/group.ldif')
        verify(c).run(
            'ldapmodify -xcD {manager_dn} -w {manager_password} '
            '-f /tmp/group.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password)
        )

        unstub()

    def test_delete_ldap_user(self):
        username = 'username'
        c = Connection('root')
        c.config.ldap_manager_dn = 'cn=manager'
        c.config.ldap_manager_password = 'managerpassword'
        c.config.ldap_group_search_base = 'ou=Group,cn=example,cn=org'
        c.config.ldap_user_search_base = 'ou=People,cn=example,cn=org'

        mocked_result = mock(Result)
        mocked_result.stdout = '''
[...]
krbprincipalname: docuser@GAUSS.RES.ENG.IT
krbticketflags: 0
memberOf: cn=group,ou=Group,dc=example,dc=org
modifiersname: cn=Manager,dc=gauss,dc=res,dc=eng,dc=it
modifytimestamp: 20180612122703Z
objectclass: posixAccount
objectclass: shadowAccount
objectclass: inetOrgPerson
objectclass: krbPrincipalAux
objectclass: krbTicketPolicyAux
[...]
        '''

        when(c).run(
            'ldapsearch -D "{manager_dn}" -w {manager_password} '
            '-b "{user_search_base}" "uid={username}" "memberOf"'.format(
                        manager_dn=c.config.ldap_manager_dn,
                        manager_password=c.config.ldap_manager_password,
                        user_search_base=c.config.ldap_user_search_base,
                        username=username
            )).thenReturn(mocked_result)

        when(c).put(ANY, '/tmp/delete_member.ldif')

        when(c).run(
            'ldapmodify -xcD "{manager_dn}" -w {manager_password} '
            '-f /tmp/delete_member.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password
              )
        )

        when(c).run(
            'ldapdelete -xcD {manager_dn} -w {manager_password} '
            '"uid={username},{user_search_base}"'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password,
                username=username,
                user_search_base=c.config.ldap_user_search_base
                )
        )

        when(c).run(
            'ldapdelete -xcD {manager_dn} -w {manager_password} '
            '"cn={username},{group_search_base}"'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password,
                username=username,
                group_search_base=c.config.ldap_group_search_base
              )
        )

        ldap.delete_ldap_user(c, username)

        verify(c).run(
            'ldapsearch -D "{manager_dn}" -w {manager_password} '
            '-b "{user_search_base}" "uid={username}" "memberOf"'.format(
                        manager_dn=c.config.ldap_manager_dn,
                        manager_password=c.config.ldap_manager_password,
                        user_search_base=c.config.ldap_user_search_base,
                        username=username
            ))

        verify(c).put(ANY, '/tmp/delete_member.ldif')

        verify(c).run(
            'ldapmodify -xcD "{manager_dn}" -w {manager_password} '
            '-f /tmp/delete_member.ldif'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password
              )
        )

        verify(c).run(
            'ldapdelete -xcD {manager_dn} -w {manager_password} '
            '"uid={username},{user_search_base}"'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password,
                username=username,
                user_search_base=c.config.ldap_user_search_base
                )
        )

        verify(c).run(
            'ldapdelete -xcD {manager_dn} -w {manager_password} '
            '"cn={username},{group_search_base}"'.format(
                manager_dn=c.config.ldap_manager_dn,
                manager_password=c.config.ldap_manager_password,
                username=username,
                group_search_base=c.config.ldap_group_search_base
              )
        )

        unstub()
