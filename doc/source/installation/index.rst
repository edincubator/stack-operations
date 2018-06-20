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

  # yum install -y krb5-server-ldap
  # cp /usr/share/doc/krb5-server-ldap-1.15.1/kerberos.schema /etc/openldap/schema/

schema_convert.conf:

.. code-block:: vim

  include /etc/openldap/schema/core.schema
  include /etc/openldap/schema/collective.schema
  include /etc/openldap/schema/corba.schema
  include /etc/openldap/schema/cosine.schema
  include /etc/openldap/schema/duaconf.schema
  include /etc/openldap/schema/dyngroup.schema
  include /etc/openldap/schema/inetorgperson.schema
  include /etc/openldap/schema/java.schema
  include /etc/openldap/schema/misc.schema
  include /etc/openldap/schema/nis.schema
  include /etc/openldap/schema/openldap.schema
  include /etc/openldap/schema/ppolicy.schema
  include /etc/openldap/schema/kerberos.schema


.. code-block:: console

  # mkdir /tmp/ldif_output
  # slapcat -f schema_convert.conf -F /tmp/ldif_output -n0 -s "cn={12}kerberos,cn=schema,cn=config" > /tmp/cn=kerberos.ldif

Edit the generated `/tmp/cn\=kerberos.ldif` file, changing the following attributes:

.. code-block:: vim

  dn: cn=kerberos,cn=schema,cn=config
  ...
  cn: kerberos

And remove the following lines from the end of the file:

.. code-block:: vim

  structuralObjectClass: olcSchemaConfig
  entryUUID: 18ccd010-746b-102d-9fbe-3760cca765dc
  creatorsName: cn=config
  createTimestamp: 20090111203515Z
  entryCSN: 20090111203515.326445Z#000000#000#000000
  modifiersName: cn=config
  modifyTimestamp: 20090111203515Z

The attribute values will vary, just be sure the attributes are removed.

.. code-block:: console

  # ldapmodify -Q -Y EXTERNAL -H ldapi:///
  dn: olcDatabase={2}hdb,cn=config
  add: olcDbIndex
  olcDbIndex: krbPrincipalName eq,pres,sub

  modifying entry "olcDatabase={2}hdb,cn=config"

  # ldapmodify -Q -Y EXTERNAL -H ldapi:///
  dn: olcDatabase={2}hdb,cn=config
  replace: olcAccess
  olcAccess: to attrs=userPassword,shadowLastChange,krbPrincipalKey by dn="cn=Manager,dc=manager,dc=edincubator,dc=eu,dc=192,dc=168,dc=51,dc=44,dc=xip,dc=io" write by anonymous auth by self write by * none
  -
  add: olcAccess
  olcAccess: to dn.base="" by * read
  -
  add: olcAccess
  olcAccess: to * by dn="cn=Manager,dc=manager,dc=edincubator,dc=eu,dc=192,dc=168,dc=51,dc=44,dc=xip,dc=io" write by * read

  modifying entry "olcDatabase={2}hdb,cn=config"


Install Kerberos:

.. code-block:: console

  # yum install -y krb5-server krb5-libs krb5-workstation
  # mkdir /etc/krb5kdc

Follow instructions at `Primary KDC Configuration <https://help.ubuntu.com/lts/serverguide/kerberos-ldap.html.en#kerberos-ldap-primary-kdc>`_.
When finished configure Kerberos service:

.. code-block:: console

  # systemctl start krb5kdc
  # systemctl start kadmin
  # systemctl enable krb5kdc
  # systemctl enable kadmin



Environment Setup (Centos 7)
----------------------------

.. code-block:: console

  # yum install -y openssh
