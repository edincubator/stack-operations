Management node
===============

System setup
------------

* Ensure that the FQDN is set checking the output of `hostname -f`
* Add FQDN from all hosts to /etc/hosts.
* Comment the following line from /etc/hosts: `127.0.0.1	<fqdn>	<hostname>`.


.. code-block:: console

  # yum -y upgrade

OpenVPN server
--------------

Follow instructions at `<https://medium.com/@gurayy/set-up-a-vpn-server-with-docker-in-5-minutes-a66184882c45>`_.

DNSMasq
-------

For installing DNSMasq, execute the following command:

.. code-block:: console

  docker run \
     --name dnsmasq \
     -d \
     --network host
     -v /root/dnsmasq/dnsmasq.conf:/etc/dnsmasq.conf \
     --log-opt "max-size=100m" \
     -e "HTTP_USER=foo" \
     -e "HTTP_PASS=bar" \
     --restart always \
     jpillora/dnsmasq

dnsmasq.conf:

.. code-block:: vim

  #dnsmasq config, for a complete example, see:
  #  http://oss.segetech.com/intra/srv/dnsmasq.conf
  #log all dns queries
  log-queries
  #use google as default nameservers
  server=8.8.4.4
  server=8.8.8.8


OpenLDAP & Kerberos
-------------------

Setup OpenLDAP
..............

* Follow steps at: https://www.server-world.info/en/note?os=CentOS_7&p=openldap&f=1
* Enable LDAP logging: http://tutoriels.meddeb.net/openldap-tutorial-log/
* Setup logrotate for LDAP log file:
    * Create `/etc/logrotate.d/slapd` file with the following content:

.. code-block:: vim

  /var/log/slapd.log {
    copytruncate
    daily
    rotate 20
    compress
    missingok
    size 10M
  }

Test logrotate configuration:

.. code-block:: console

 # logrotate -vf /etc/logrotate.d/slapd

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

  # docker run -p 6443:443 --name phpldapadmin  \
    -v /root/phpldapadmin/certs:/container/service/ldap-client/assets/certs \
    -v /root/phpldapadmin/certs:/container/service/phpldapadmin/assets/apache2/certs \
    --env PHPLDAPADMIN_LDAP_HOSTS=<ldap_host>  \
    --restart always \
    --detach osixia/phpldapadmin:0.7.2

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


Load the new schema with ldapadd:

.. code-block:: console

  # sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f /tmp/cn\=kerberos.ldif

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

Change Kerbero's admin principal password:

.. code-block:: console

  # sudo kadmin.local
  kadmin.local:  cpw kadmin/admin@EDINCUBATOR.EU
  Enter password for principal "kadmin/admin@EDINCUBATOR.EU":
  Re-enter password for principal "kadmin/admin@EDINCUBATOR.EU":
  Password for "kadmin/admin@EDINCUBATOR.EU" changed.
  kadmin.local:

Edit `/var/kerberos/krb5kdc/kadm5.acl`:

.. code-block:: vim

  */admin@EDINCUBATOR.EU	e*


.. warning::

  You must let Ambari managing `/etc/krb5.conf` but *add your custom LDAP sections!*


Installing Ambari
-----------------

Follow steps at https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.2.2/bk_ambari-installation/content/ch_Getting_Ready.html.
Before deploying a cluster, enable LDAP and SSL at Ambari.

Enabling LDAP for Ambari
........................

Follow steps at https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.2.2/bk_ambari-security/content/configuring_ambari_for_ldap_or_active_directory_authentication.html.

.. note::

  Import server.crt certificate into Ambari LDAPS keystore:
  $JAVA_HOME/bin/keytool -import -trustcacerts -alias root -file /etc/openldap/certs/server.crt -keystore /etc/ambari-server/keys/ldaps-keystore.jks

Enabling SSL for Ambari
.......................

Follow steps at https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.2.2/bk_ambari-security/content/optional_set_up_ssl_for_ambari.html.

.. warning::

  When adding nodes to the cluster, an SSL error might appear. Follow instructions
  at `<https://community.hortonworks.com/content/supportkb/208283/error-2018-07-16-005228887-netutilpy96-eof-occurre.html>`_
  to solve it.

Deploying a cluster
...................

After enabling LDAP and SSL, follow the following steps for deploying a cluster: https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.2.2/bk_ambari-installation/content/ch_Deploy_and_Configure_a_HDP_Cluster.html.
Deploy only the minimal components before enabling Kerberos (Zookeeper + HDFS).
It is recommended to install clients in all nodes.


Enabling Kerberos for Ambari
............................

Follow steps at https://docs.hortonworks.com/HDPDocuments/Ambari-2.6.2.2/bk_ambari-security/content/ch_configuring_amb_hdp_for_kerberos.html.

.. warning::

  Disable `Manage Kerberos client krb5.conf` under `Advanced krb5-conf`.

After enabling Kerberos, proceed to deploy the rest of the components of the cluster.


Installing MySQL and enabling on Ambari
.......................................

Follow tutorial at: https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-centos-7

Library need by Ambari:

.. code-block:: console

  # wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.11.tar.gz
  # tar -xf mysql-connector-java-8.0.11.tar.gz

For tools that need a MySQL database:

.. code-block:: console

  # CREATE DATABASE <databasename>;
  # CREATE USER '<username>'@'%' IDENTIFIED BY '<password>';
  # GRANT ALL ON <databasename>.* TO '<username>'@'%';



Installing NiFi
---------------

Not documented because it doesn't work with two hops (VM -> Host Server -> My laptop)


Enabling SSL for Ranger
-----------------------

* Follow instructions at: https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.0/bk_security/content/configure_ambari_ranger_ssl.html.
* How to convert trustedCertEntry into privateKeyEntry: https://www.manualesfaciles.com/gestionar-certificado-como-privatekeyentry/.


Configuring Ranger plugins for SSL
..................................

* Enable plugin at Ranger config.
* Export Ranger certificate:

.. code-block:: console

 # $JAVA_HOME/bin/keytool -export -keystore ranger-admin-keystore.jks -alias <cert-alias> -file /etc/security/certs/ranger/ranger-admin-trust.cer

* For each plugin, create plugin keystore and truststore and import Ranger certificate:

.. code-block:: console

  # keytool -genkey -keyalg RSA -alias ranger<tool>Agent -keystore ranger-<tool>-keystore.jks -storepass <myKeyFilePassword> -validity 360 -keysize 2048
  # chown <toolUser>:<toolGroup> ranger-<tool>-keystore.jks
  # chmod 400 ranger-<tool>-keystore.jks
  # keytool -import -file ranger-admin-trust.cer -alias <cert-alias> -keystore ranger-<tool>-truststore.jks -storepass <trustStorePassword>
  # chown <toolUser>:<toolGroup> ranger-<tool>-truststore.jks
  # chmod 400 ranger-<tool>-truststore.jks


* Configure `Advanced ranger-<tool>-policymgr-ssl` at tool's configuration:

.. code-block:: properties

  xasecure.policymgr.clientssl.keystore=/etc/security/certs/ranger/ranger-<tool>-keystore.jks
  xasecure.policymgr.clientssl.keystore.password=<myKeyFilePassword>
  xasecure.policymgr.clientssl.truststore=/etc/security/certs/ranger/ranger-<tool>-truststore.jks
  xasecure.policymgr.clientssl.truststore.password=<trustStorePassword>

* Import tool's certificate into ranger:

.. code-block:: console

  # keytool -export -keystore ranger-<tool>-keystore.jks -alias ranger<tool>Agent -file ranger-<tool>-trust.cer
  # keytool -import -file ranger-<tool>-trust.cer -alias ranger<tool>AgentTrust -keystore /usr/hdp/current/ranger-admin/conf/ranger-admin-keystore.jks


* Give proper access rights to `.cred.jceks.crc` file at `/etc/ranger/<plugin >/`.

* Restart Ranger and HDFS.


Zeppelin
--------

* Install Zeppelin through Ambari.
* Set `zeppelin.interpreter.config.upgrade` to false in `Advanced zeppelin-config`.
* In `shiro_ini_content` from `Advanced zeppelin-shiro-ini`, replace admin's
  password and comment other users, set the following LDAP properties and URL
  permissions.

.. code-block:: ini

  ### A sample for configuring LDAP Directory Realm
  ldapRealm = org.apache.zeppelin.realm.LdapGroupRealm
  ## search base for ldap groups (only relevant for LdapGroupRealm):
  ldapRealm.contextFactory.environment[ldap.searchBase] = ou=People,dc=....
  ldapRealm.contextFactory.url = ldaps://host:636
  ldapRealm.userDnTemplate = uid={0},ou=People,dc=....
  ldapRealm.contextFactory.authenticationMechanism = SIMPLE

  [urls]
  # This section is used for url-based security.
  # You can secure interpreter, configuration and credential information by urls. Comment or uncomment the below urls that you want to hide.
  # anon means the access is anonymous.
  # authc means Form based Auth Security
  # To enfore security, comment the line below and uncomment the next one
  /api/version = anon
  /api/interpreter/** = authc, roles[admin]
  /api/configurations/** = authc, roles[admin]
  /api/credential/** = authc, roles[admin]
  #/** = anon
  /** = authc

* Include the certificate from LDAPS in JAVA keystore.
* At Zeppelin web UI, disable sh and spark interpreters.
