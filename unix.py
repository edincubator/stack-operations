def create_unix_user(c, username):
    c.run('adduser {}'.format(username))
    c.run('usermod -s /sbin/nologin {}'.format(username))