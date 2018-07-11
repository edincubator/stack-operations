import json
import smtplib
from email.mime.text import MIMEText

import invoke
from fabric.connection import Connection
from mockito import ANY, mock, unstub, verify, when
from mockito.matchers import captor
from operations import hdfs, kerberos, ldap, ranger, unix, user


class TestUser(object):
    def test_new_no_group(self):
        username = 'username'
        usermail = 'user@mail.com'
        folder_uuid = 'folder_uuid'
        file_uuid = 'file_uuid'
        user_mail = 'user@mail.com'

        c = Connection('root')
        c.config.hosts = ['host1', 'host2', 'host3']
        c.config.ldap_host = 'ldap.host'
        c.config.kerberos_host = 'kerberos.host'
        c.config.master_host = 'master.host'
        c.config.ranger_host = 'ranger.host'

        ldap_connection = captor(ANY(Connection))
        kerberos_create_connection = captor(ANY(Connection))
        kerberos_nifi_connection = captor(ANY(Connection))
        ranger_update_connection = captor(ANY(Connection))
        hdfs_connection = captor(ANY(Connection))
        ranger_create_connection = captor(ANY(Connection))
        ranger_nifi_connection = captor(ANY(Connection))
        ambari_connection = captor(ANY(Connection))
        mail_connection = captor(ANY(Connection))

        when(unix).create_unix_user(ANY(Connection), username)
        when(ldap).create_ldap_user(ldap_connection, username, ANY)
        when(kerberos).create_kerberos_user(
            kerberos_create_connection, username, ANY)
        when(kerberos).create_nifi_keytab(
            kerberos_nifi_connection, username).thenReturn(
                (folder_uuid, file_uuid))
        when(ranger).update_ranger_usersync(ranger_update_connection)
        when(hdfs).create_hdfs_home(hdfs_connection, username)
        when(ranger).create_ranger_policy(
            ranger_create_connection,
            ['/user/{}'.format(username)],
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop')
        when(ranger).update_nifi_flow_ranger_policy(
            ranger_nifi_connection, username)
        when(user).sync_ambari_users(ambari_connection)
        when(user).send_password_mail(mail_connection, username, ANY,
                                      user_mail, folder_uuid, file_uuid)

        user.new(c, username, usermail)

        assert ldap_connection.value.host == c.config.ldap_host
        assert kerberos_create_connection.value.host == c.config.kerberos_host
        assert kerberos_nifi_connection.value.host == c.config.master_host
        assert ranger_update_connection.value.host == c.config.ranger_host
        assert hdfs_connection.value.host == c.config.master_host
        assert ranger_create_connection.value.host == c.host
        assert ranger_nifi_connection.value.host == c.host
        assert ambari_connection.value.host == c.host
        assert mail_connection.value.host == c.host

        verify(unix, times=3).create_unix_user(ANY(Connection), username)
        verify(ldap).create_ldap_user(ldap_connection, username, ANY)
        verify(kerberos).create_kerberos_user(
            kerberos_create_connection, username, ANY)
        verify(kerberos).create_nifi_keytab(kerberos_nifi_connection, username)
        verify(ranger).update_ranger_usersync(ranger_update_connection)
        verify(hdfs).create_hdfs_home(hdfs_connection, username)
        verify(ranger).create_ranger_policy(
            ranger_create_connection,
            ['/user/{}'.format(username)],
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop')
        verify(ranger).update_nifi_flow_ranger_policy(
            ranger_nifi_connection, username)
        verify(user).sync_ambari_users(ambari_connection)
        verify(user).send_password_mail(mail_connection, username, ANY,
                                        user_mail, folder_uuid, file_uuid)

        verify(ldap, times=0).add_user_to_ldap_group()

        unstub()

    def test_new_group(self):
        username = 'username'
        usermail = 'user@mail.com'
        folder_uuid = 'folder_uuid'
        file_uuid = 'file_uuid'
        user_mail = 'user@mail.com'
        group = 'group'

        c = Connection('root')
        c.config.hosts = ['host1', 'host2', 'host3']
        c.config.ldap_host = 'ldap.host'
        c.config.kerberos_host = 'kerberos.host'
        c.config.master_host = 'master.host'
        c.config.ranger_host = 'ranger.host'

        ldap_connection = captor(ANY(Connection))
        ldap_group_connection = captor(ANY(Connection))
        kerberos_create_connection = captor(ANY(Connection))
        kerberos_nifi_connection = captor(ANY(Connection))
        ranger_update_connection = captor(ANY(Connection))
        hdfs_connection = captor(ANY(Connection))
        ranger_create_connection = captor(ANY(Connection))
        ranger_nifi_connection = captor(ANY(Connection))
        ambari_connection = captor(ANY(Connection))
        mail_connection = captor(ANY(Connection))

        when(unix).create_unix_user(ANY(Connection), username)
        when(ldap).create_ldap_user(ldap_connection, username, ANY)
        when(ldap).add_user_to_ldap_group(
            ldap_group_connection, username, group)
        when(kerberos).create_kerberos_user(
            kerberos_create_connection, username, ANY)
        when(kerberos).create_nifi_keytab(
            kerberos_nifi_connection, username).thenReturn(
                (folder_uuid, file_uuid))
        when(ranger).update_ranger_usersync(ranger_update_connection)
        when(hdfs).create_hdfs_home(hdfs_connection, username)
        when(ranger).create_ranger_policy(
            ranger_create_connection,
            ['/user/{}'.format(username)],
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop')
        when(ranger).update_nifi_flow_ranger_policy(
            ranger_nifi_connection, username)
        when(user).sync_ambari_users(ambari_connection)
        when(user).send_password_mail(mail_connection, username, ANY,
                                      user_mail, folder_uuid, file_uuid)

        user.new(c, username, usermail, group)

        assert ldap_connection.value.host == c.config.ldap_host
        assert ldap_group_connection.value.host == c.config.ldap_host
        assert kerberos_create_connection.value.host == c.config.kerberos_host
        assert kerberos_nifi_connection.value.host == c.config.master_host
        assert ranger_update_connection.value.host == c.config.ranger_host
        assert hdfs_connection.value.host == c.config.master_host
        assert ranger_create_connection.value.host == c.host
        assert ranger_nifi_connection.value.host == c.host
        assert ambari_connection.value.host == c.host
        assert mail_connection.value.host == c.host

        verify(unix, times=3).create_unix_user(ANY(Connection), username)
        verify(ldap).create_ldap_user(ldap_connection, username, ANY)
        verify(ldap).add_user_to_ldap_group(
            ldap_group_connection, username, group)
        verify(kerberos).create_kerberos_user(
            kerberos_create_connection, username, ANY)
        verify(kerberos).create_nifi_keytab(kerberos_nifi_connection, username)
        verify(ranger).update_ranger_usersync(ranger_update_connection)
        verify(hdfs).create_hdfs_home(hdfs_connection, username)
        verify(ranger).create_ranger_policy(
            ranger_create_connection,
            ['/user/{}'.format(username)],
            username,
            'hdfs_home_{}'.format(username),
            'HDFS home directory for user {}'.format(username),
            'path',
            'hadoop')
        verify(ranger).update_nifi_flow_ranger_policy(
            ranger_nifi_connection, username)
        verify(user).sync_ambari_users(ambari_connection)
        verify(user).send_password_mail(mail_connection, username, ANY,
                                        user_mail, folder_uuid, file_uuid)

        verify(ldap, times=0).add_user_to_ldap_group()

        unstub()

    def test_sync_ambari_users(self):
        c = Connection('root')
        c.config.ambari_url = 'http://fake-ambari-url'
        content = [
            {"Event":
                {"specs":
                    [{"principal_type": "users", "sync_type": "all"},
                     {"principal_type": "groups", "sync_type": "all"}]
                 }
             }]
        when(invoke).run(
            "curl -u admin -H 'X-Requested-By: ambari' -X POST -d "
            "'{content}' {ambari_url}/api/v1/ldap_sync_events".format(
                content=json.dumps(content),
                ambari_url=c.config.ambari_url), pty=True)
        user.sync_ambari_users(c)

        verify(invoke, times=1).run(
            "curl -u admin -H 'X-Requested-By: ambari' -X POST -d "
            "'{content}' {ambari_url}/api/v1/ldap_sync_events".format(
                content=json.dumps(content),
                ambari_url=c.config.ambari_url), pty=True
        )

        unstub()

    def test_send_password_mail(self):
        user_mail = 'user@mail.com'
        username = 'username'
        password = 'password'
        folder_uuid = 'folder_uuid'
        file_uuid = 'file_uuid'

        c = Connection('root')
        c.config.kerberos_realm = 'EXAMPLE.ORG'
        c.config.mail_from = 'admin@foo.org'
        c.config.mail_host = 'smtp.foo.bar'
        c.config.mail_port = '500'
        c.config.mail_user = 'foo'
        c.config.mail_password = 'secretpassword'

        principal = '{username}@{realm}'.format(username=username,
                                                realm=c.config.kerberos_realm)
        msg = MIMEText('''Welcome to EDI Big Data Stack!\n\n
Those are your credentials for accesing to the system:\n\n
LDAP username: {username}\n
Kerberos Principal: {principal}\n
Password: {password}\n
NiFi keytab: {keytab}'''.format(
            username=username,
            principal=principal,
            password=password,
            keytab='{folder_uuid}/{file_uuid}.keytab'.format(
                folder_uuid=folder_uuid,
                file_uuid=file_uuid
            )))
        msg['Subject'] = "[European Data Incubator] Big Data Stack Credentials"
        msg['From'] = "EDI - European Data Incubator <{}>".format(
            c.config.mail_from)
        msg['To'] = user_mail

        server = mock(smtplib.SMTP)
        when(server).login(c.config.mail_user, c.config.mail_password)
        when(server).sendmail(c.config.mail_from, [user_mail], msg.as_string())
        when(server).quit()

        when(smtplib).SMTP(
            c.config.mail_host, c.config.mail_port).thenReturn(server)

        user.send_password_mail(
            c, username, password, user_mail, folder_uuid, file_uuid)

        verify(smtplib, times=1).SMTP(c.config.mail_host, c.config.mail_port)
        verify(server, times=1).login(
            c.config.mail_user, c.config.mail_password)
        verify(server, times=1).sendmail(
            c.config.mail_from, [user_mail], msg.as_string())
        verify(server, times=1).quit()

        unstub()
