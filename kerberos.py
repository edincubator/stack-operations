import uuid

import settings


def create_kerberos_user(c, username, password):
    c.run('kadmin -p {admin_principal} -w {admin_password} addprinc -x '
          'dn="uid={username},{user_search_base}" -pw {password} '
          '{username}'.format(
            username=username,
            user_search_base=settings.ldap_user_search_base,
            password=password,
            admin_principal=settings.kerberos_admin_principal,
            admin_password=settings.kerberos_admin_password), pty=True
          )


def create_nifi_keytab(c, username):
    folder_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, settings.master_host)
    file_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, settings.master_host)
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)

    c.run('mkdir /home/nifi/{folder_uuid}'.format(folder_uuid=folder_uuid))

    c.run('kadmin -p {admin_principal} -w {admin_password} -q "xst '
          '-norandkey -k /home/nifi/{folder_uuid}/{file_uuid}.keytab '
          '{principal}"'.format(
            admin_principal=settings.kerberos_admin_principal,
            admin_password=settings.kerberos_admin_password,
            folder_uuid=folder_uuid,
            file_uuid=file_uuid,
            principal=principal
          ))
    c.run('chown {username}:hadoop /home/nifi/{folder_uuid}/'
          '{file_uuid}.keytab'.format(
            username=username,
            folder_uuid=folder_uuid,
            file_uuid=file_uuid
          ))
    c.run('chmod 400 /home/nifi/{folder_uuid}/{file_uuid}.keytab'.format(
        folder_uuid=folder_uuid, file_uuid=file_uuid
    ))

    return folder_uuid, file_uuid
