import uuid
import settings
import smtplib
from email.mime.text import MIMEText
from fabric.api import run, env, execute
from fabric.decorators import task, roles


env.user = 'root'
env.roledefs = {
    'hosts': settings.hosts,
    'kerberos': settings.kerberos_host,
}


@task
def create_user(username, mail):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)

    kpass = execute(create_kerberos_user,
                    ('{username}@{realm}'.format(
                        username=username,
                        realm=settings.kerberos_realm)))

    execute(create_unix_user, username)
    execute(send_password_mail, username, principal,
            str(kpass.get(settings.kerberos_host[0])), mail)


@roles('hosts')
def create_unix_user(username):
    run('adduser {}'.format(username))
    run('usermod -s /sbin/nologin {}'.format(username))


@roles('kerberos')
def create_kerberos_user(principal, password=None):
    if password is None:
        password = uuid.uuid4()
    run('kadmin addprinc -pw {password} +needchange {principal}'.format(
        password=password, principal=principal))
    return password


def send_password_mail(username, principal, password, mail):
    msg = MIMEText('''Welcome to EDI Big Data Stack!\n\n
Those are your Kerberos credentials for accesing to the system:\n\n
Principal: {principal}\n
Password: {password}'''.format(mail_from=settings.mail_from, to=mail,
                               principal=principal,
                               password=password))
    msg['Subject'] = "[European Data Incubator] Big Data Stack Credentials"
    msg['From'] = "EDI - European Data Incubator <{}>".format(
        settings.mail_from)
    msg['To'] = mail

    server = smtplib.SMTP(settings.mail_host, settings.mail_port)
    if settings.mail_user is not None:
        server.login(settings.mail_user, settings.mail_password)
    server.sendmail(settings.mail_from, [mail], msg.as_string())
    server.quit()


@task
def delete_user(username):
    principal = '{username}@{realm}'.format(username=username,
                                            realm=settings.kerberos_realm)
    execute(delete_kerberos_user, principal)
    execute(delete_unix_user, username)


@roles('hosts')
def delete_unix_user(username):
    run('userdel {}'.format(username))


@roles('kerberos')
def delete_kerberos_user(principal):
    run('kadmin delete_principal {}'.format(principal))
