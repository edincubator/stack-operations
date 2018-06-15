import hashlib
import os
import StringIO
from string import Template

import settings


def create_ldap_user(c, username, password):
    uid = c.run('id -u {}'.format(username)).stdout.strip()
    gid = c.run('id -u {}'.format(username)).stdout.strip()

    args = {'username': username,
            'group_search_base': settings.ldap_group_search_base,
            'gid': gid,
            'user_search_base': settings.ldap_user_search_base,
            'uid': uid,
            'password': make_secret(password)}

    filein = open('ldap_template/user.ldif')
    template = Template(filein.read())
    user_ldif = template.substitute(args)

    output = StringIO.StringIO()
    output.write(user_ldif)

    c.put(output, '/tmp/user.ldif')

    c.run('ldapadd -cxD {manager_dn} -w {manager_password} '
          '-f /tmp/user.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


def add_user_to_ldap_group(c, username, group):
    args = {'group': group,
            'group_search_base': settings.ldap_group_search_base,
            'username': username,
            'user_search_base': settings.ldap_user_search_base}

    filein = open('ldap_template/group.ldif')
    template = Template(filein.read())
    group_ldif = template.substitute(args)

    output = StringIO.StringIO()
    output.write(group_ldif)

    c.put(output, '/tmp/group.ldif')

    c.run('ldapmodify -xcD {manager_dn} -w {manager_password} '
          '-f /tmp/group.ldif'.format(
            manager_dn=settings.ldap_manager_dn,
            manager_password=settings.ldap_manager_password))


def make_secret(password):
    """
    Encodes the given password as a base64 SSHA hash+salt buffer
    """
    salt = os.urandom(4)

    # hash the password and append the salt
    sha = hashlib.sha1(password)
    sha.update(salt)

    # create a base64 encoded string of the concatenated digest + salt
    digest_salt_b64 = '{}{}'.format(sha.digest(),
                                    salt).encode('base64').strip()

    return digest_salt_b64
