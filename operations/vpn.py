def create_user(c, username):
    c.run('docker run -v {vpn_data_dir}:/etc/openvpn --rm '
          '{vpn_container_name} easyrsa build-client-full '
          '{username} nopass'.format(
            vpn_data_dir=c.vpn_data_dir,
            vpn_container_name=c.vpn_image_name,
            username=username
            ))

    return c.run(
        'docker run -v {vpn_data_dir}:/etc/openvpn '
        '--rm {vpn_container_name} ovpn_getclient {username}'.format(
            vpn_data_dir=c.vpn_data_dir,
            vpn_container_name=c.vpn_image_name,
            username=username
        )).stdout
