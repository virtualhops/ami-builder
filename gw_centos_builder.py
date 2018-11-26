import os
import sys
import textwrap
from parser_for_builder import config_value, find, find_first_in_file, load_config, parse_args, run, validate_args

parser = parse_args(sys.argv[1:])
validate_args(parser)
config = load_config(parser.config_path)    

if __name__ == '__main__':
    run('yum install -y systemd-networkd')
    run('systemctl enable systemd-networkd')
    run('systemctl restart systemd-networkd')

    upgrade_kernel = config_value(config, 'contrail_configuration.UPGRADE_KERNEL', False)
    kernel_version = config_value(config, 'contrail_configuration.KERNEL_VERSION', None)
    kernel_packages = list()
    if upgrade_kernel:
        if kernel_version:
            kernel_packages.append('kernel-' + kernel_version)
            kernel_packages.append('kernel-tools-' + kernel_version)
            kernel_packages.append('kernel-tools-libs-' + kernel_version)
        else:
            kernel_packages.append('kernel')
            kernel_packages.append('kernel-tools')
            kernel_packages.append('kernel-tools-libs')
        for package in kernel_packages:
            run('yum install -y ' + package)

    grub_kernel_file = find_first_in_file(r'/boot/vmlinuz-(\S+)', '/boot/grub2/grub.cfg')

    if not grub_kernel_file:
        raise Exception("ERROR: Could not find next boot's kernel version in /boot/grub2/grub.cfg")
    else:
        grub_kernel_version = grub_kernel_file.group(1)

    run('yum install -y yum-plugin-versionlock')
    run('yum versionlock kernel-' + grub_kernel_version)
    run('yum versionlock kernel-tools-' + grub_kernel_version)
    run('yum versionlock kernel-tools-libs' + grub_kernel_version)

    run('yum install -y epel-release')
    run('yum install -y openssl')
    run('yum install -y python-pip')
    run('yum install -y yum-utils')
    run('yum install -y device-mapper-persistent-data')
    run('yum install -y lvm2')
    run('pip install --upgrade pip')

    docker_repo = '''\
    [docker]
    name=Docker Repository
    baseurl=https://download.docker.com/linux/centos/7/$basearch/stable
    enabled=1
    gpgcheck=1
    gpgkey=https://download.docker.com/linux/centos/gpg
   '''

    with open('/etc/yum.repos.d/docker.repo', 'w') as fh:
        fh.write(textwrap.dedent(docker_repo))

    run('yum-config-manager --enable docker')
    run('yum install -y docker-ce-18.03.1.ce')
    run('pip install docker-compose==1.9.0')
    container_registry = config_value(config, 'global_configuration.CONTAINER_REGISTRY', 'opencontrailnightly')
    container_registry_username = config_value(config, 'global_configuration.CONTAINER_REGISTRY_USERNAME', None)
    container_registry_password = config_value(config, 'global_configuration.CONTAINER_REGISTRY_PASSWORD', None)
    registry_private_insecure = config_value(config, 'global_configuration.REGISTRY_PRIVATE_INSECURE', None)
    registry_private_secure = config_value(config, 'global_configuration.REGISTRY_PRIVATE_SECURE', None)

    run('systemctl start docker')
    if container_registry and container_registry_username and container_registry_password:
        run('docker login --username {0} --password {1} {2}'.\
        format(container_registry_username, container_registry_password, container_registry))

    run('yum install -y iptables-services')
    if os.path.exists('/sbin/firewalld'):
        run('systemctl stop firewalld')
        run('systemctl disable firewalld')
    
    run('pip install jinja2')
    run('pip install pyOpenSSL')
    with open('/etc/modules-load.d/strongswan.conf', 'w') as fh:
        fh.write('xfrm_user\n')
        fh.write('af_key\n')

    run('modprobe xfrm_user')
    run('modprobe af_key')

    contrail_multicloud_version = config_value(config, 'multicloud_configuration.CONTRAIL_MULTICLOUD_VERSION', 'latest')

    run('docker pull {0}/contrail-multicloud-openvpn:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-multicloud-strongswan:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-multicloud-vrrp:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-multicloud-bird:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-vrouter-agent:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-vrouter-kernel-init:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-node-init:{1}'.format(container_registry,contrail_multicloud_version))
    run('docker pull {0}/contrail-nodemgr:{1}'.format(container_registry,contrail_multicloud_version))
