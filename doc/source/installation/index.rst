Big Data Stack installation
===========================

System setup
------------

  * Ensure that the FQDN is set: hostname -f

.. code-block:: console

  # yum -y upgrade

OpenLDAP & Kerberos
-------------------

Setup OpenLDAP
..............

* Follow steps at: https://www.server-world.info/en/note?os=CentOS_7&p=openldap&f=1
* Enable LDAP logging: http://tutoriels.meddeb.net/openldap-tutorial-log/

Setup memberOf attribute support
................................

.. code-block:: vim

  # /root/15-memberof.ldif
  dn: cn=module,cn=config
  cn: module
  objectClass: olcModuleList
  objectclass: top
  olcModuleLoad: memberof.la
  olcModulePath: /usr/lib64/openldap

  dn: olcOverlay=memberof,olcDatabase={2}hdb,cn=config
  objectclass: olcconfig
  objectclass: olcMemberOf
  objectclass: olcoverlayconfig
  objectclass: top
  olcoverlay: memberof

.. code-block:: console

  # ldapadd -Y EXTERNAL -H ldapi:/// -f 15-memberof.ldif


Setup OpenLDAP over TLS
.......................

* (Optional, only if self-signed certificates are used) Create SSL certificate: https://www.server-world.info/en/note?os=CentOS_7&p=ssl
* Configure LDAP over TLS (server only, not client): https://www.server-world.info/en/note?os=CentOS_7&p=openldap&f=4

.. code-block:: vim

  # /etc/openldap/ldap.conf
  #
  # LDAP Defaults
  #

  # See ldap.conf(5) for details
  # This file should be world readable but not world writable.

  #BASE	dc=example,dc=com
  #URI	ldap://ldap.example.com ldap://ldap-master.example.com:666

  #SIZELIMIT	12
  #TIMELIMIT	15
  #DEREF		never

  TLS_CACERTDIR /etc/openldap/certs

  # Turning this off breaks GSSAPI used with krb5 when rdns = false
  SASL_NOCANON	on
  TLS_REQCERT allow


phpLDAPAdmin
............

* Install Docker: https://docs.docker.com/install/linux/docker-ce/centos/#prerequisites

Install phpLDAPAdmin:

.. code-block:: console

  # docker run -P \
       --env PHPLDAPADMIN_LDAP_HOSTS=<ldap-host> \
       --detach osixia/phpldapadmin:0.7.1

phpLDAP admin is available at https://host:port.


Kerberos
........

.. code-block:: console

  # yum install krb5-server-ldap

Environment Setup (Centos 7)
----------------------------

.. code-block:: console

  # yum install -y openssh
