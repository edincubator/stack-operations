Managed node
============

* Ensure that the FQDN is set checking the output of `hostname -f`.
* Add all hostnames' FDQN to /etc/hosts.
* Comment the following line from /etc/hosts: `127.0.0.1	<fqdn>	<hostname>`.
* Export public RSA key from Ambari Server to managed nodes' `authorized_keys` file.
* Copy management server certificate to all nodes: https://serverfault.com/questions/730006/how-do-i-trust-a-self-signed-certificate.
