import uuid

from fabric.connection import Connection
from mockito import unstub, verify, when
from operations import kerberos


class TestKerberos(object):
    def test_create_kerberos_user(self):
        username = 'username'
        password = 'password'
        c = Connection('root')
        c.config.ldap_user_search_base = 'ou=Group,cn=example,cn=org'
        c.config.kerberos_admin_principal = 'kadmin/admin@EXAMPLE.ORG'
        c.config.kerberos_admin_password = 'kerberospassword'

        when(c).run(
            'kadmin -p {admin_principal} -w {admin_password} addprinc -x '
            'dn="uid={username},{user_search_base}" -pw {password} '
            '{username}'.format(
                username=username,
                user_search_base=c.config.ldap_user_search_base,
                password=password,
                admin_principal=c.config.kerberos_admin_principal,
                admin_password=c.config.kerberos_admin_password), pty=True
              )

        kerberos.create_kerberos_user(c, username, password)

        verify(c).run(
            'kadmin -p {admin_principal} -w {admin_password} addprinc -x '
            'dn="uid={username},{user_search_base}" -pw {password} '
            '{username}'.format(
                username=username,
                user_search_base=c.config.ldap_user_search_base,
                password=password,
                admin_principal=c.config.kerberos_admin_principal,
                admin_password=c.config.kerberos_admin_password), pty=True
              )
        unstub()

    def test_create_nifi_keytab(self):
        username = 'username'
        mocked_uuid = 'mocked_uuid'

        when(uuid).uuid1().thenReturn(mocked_uuid)

        c = Connection('root')
        c.config.kerberos_realm = 'EXAMPLE.ORG'
        c.config.kerberos_admin_principal = 'kadmin/admin@EXAMPLE.ORG'
        c.config.kerberos_admin_password = 'kerberospassword'

        principal = '{username}@{realm}'.format(username=username,
                                                realm=c.config.kerberos_realm)

        when(c).run('mkdir /home/nifi/{folder_uuid}'.format(
            folder_uuid=mocked_uuid))

        when(c).run(
            'kadmin -p {admin_principal} -w {admin_password} -q "xst '
            '-norandkey -k /home/nifi/{folder_uuid}/{file_uuid}.keytab '
            '{principal}"'.format(
                admin_principal=c.config.kerberos_admin_principal,
                admin_password=c.config.kerberos_admin_password,
                folder_uuid=mocked_uuid,
                file_uuid=mocked_uuid,
                principal=principal
            )
        )

        when(c).run(
            'chown {username}:hadoop /home/nifi/{folder_uuid}/'
            '{file_uuid}.keytab'.format(
                username=username,
                folder_uuid=mocked_uuid,
                file_uuid=mocked_uuid
            )
        )

        when(c).run(
            'chmod 400 /home/nifi/{folder_uuid}/{file_uuid}.keytab'.format(
                folder_uuid=mocked_uuid, file_uuid=mocked_uuid
            )
        )

        kerberos.create_nifi_keytab(c, username)

        verify(c).run('mkdir /home/nifi/{folder_uuid}'.format(
            folder_uuid=mocked_uuid))

        verify(c).run(
            'kadmin -p {admin_principal} -w {admin_password} -q "xst '
            '-norandkey -k /home/nifi/{folder_uuid}/{file_uuid}.keytab '
            '{principal}"'.format(
                admin_principal=c.config.kerberos_admin_principal,
                admin_password=c.config.kerberos_admin_password,
                folder_uuid=mocked_uuid,
                file_uuid=mocked_uuid,
                principal=principal
            )
        )

        verify(c).run(
            'chown {username}:hadoop /home/nifi/{folder_uuid}/'
            '{file_uuid}.keytab'.format(
                username=username,
                folder_uuid=mocked_uuid,
                file_uuid=mocked_uuid
            )
        )

        verify(c).run(
            'chmod 400 /home/nifi/{folder_uuid}/{file_uuid}.keytab'.format(
                folder_uuid=mocked_uuid, file_uuid=mocked_uuid
            )
        )

        unstub()
