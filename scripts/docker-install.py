# import argparse
import os
import subprocess


def get_os_info():
    os_info = {}
    with open('/etc/os-release') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            os_info[key] = value.strip('"')
    return os_info


def install_docker_ubuntu():
    # Install Docker
    print("Installing Docker.")
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get install', 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common', '-y'])
    subprocess.run(['curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '|', 'sudo', 'gpg', '--dearmor', '-o', '/usr/share/keyrings/docker-archive-keyring.gpg'])
    subprocess.run(['echo', '"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', '|', 'sudo', 'tee', '/etc/apt/sources.list.d/docker.list', '>', '/dev/null'])
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get', 'install', 'docker-ce', 'docker-ce-cli', 'containerd.io', '-y'])
    print("Docker installed.")

    # Add user to docker group
    print("Add your user to the docker group")
    subprocess.run(['sudo', 'groupadd', 'docker'])
    subprocess.run(['sudo', 'usermod', '-aG', 'docker', '$USER'])
    subprocess.run(['newgrp', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'docker'])
    print("User added to docker group.")

    # Install Docker Compose
    print("Installing Docker Compose.")
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'curl', '-L', '"https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)"', '-o', '/usr/local/bin/docker-compose'])
    subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/docker-compose'])
    subprocess.run(['sudo', 'ln', '-s', '/usr/local/bin/docker-compose', '/usr/bin/docker-compose'])
    print("Docker Compose installed.")

    # Ask for main path
    main_path = input("Enter the main path for the storage system. This script will create a /docker folder where all the docker images will be stored: ")
    if not main_path:
        print("Error: No path provided.")
        return
    if not os.path.exists(main_path):
        print(f"Error: The path {main_path} does not exist.")
        return

    docker_path = os.path.join(main_path, 'docker')
    subprocess.run(['sudo', 'mkdir', docker_path])

    print("Changing Docker Root Dir.")
    subprocess.run(['sudo', 'systemctl', 'stop', 'docker'])
    subprocess.run(['sudo', 'mv', '/var/lib/docker', docker_path])
    subprocess.run(['sudo', 'ln', '-s', docker_path, '/var/lib/docker'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'docker', 'info', '|', 'grep', '"Docker Root Dir"'])


def install_docker_rocky():
    # Install Docker
    print("Installing Docker.")
    subprocess.run(['sudo', 'dnf', 'check-update'])
    subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo', 'https://download.docker.com/linux/centos/docker-ce.repo'])
    subprocess.run(['sudo', 'dnf', 'install', 'docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-compose-plugin', '-y'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'docker'])
    print("Docker installed.")

    # Add user to docker group
    print("Add your user to the docker group")
    subprocess.run(['sudo', 'groupadd', 'docker'])
    subprocess.run(['sudo', 'usermod', '-aG', 'docker', '$USER'])
    subprocess.run(['newgrp', 'docker'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'docker'])
    print("User added to docker group.")

    # Ask for main path
    main_path = input("Enter the main path for the storage system. This script will create a /docker folder where all the docker images will be stored: ")
    if not main_path:
        print("Error: No path provided.")
        return
    if not os.path.exists(main_path):
        print(f"Error: The path {main_path} does not exist.")
        return

    docker_path = os.path.join(main_path, 'docker')
    subprocess.run(['sudo', 'mkdir', docker_path])

    print("Changing Docker Root Dir.")
    subprocess.run(['sudo', 'systemctl', 'stop', 'docker'])
    subprocess.run(['sudo', 'mv', '/var/lib/docker', docker_path])
    subprocess.run(['sudo', 'ln', '-s', docker_path, '/var/lib/docker'])
    subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
    subprocess.run(['sudo', 'docker', 'info', '|', 'grep', '"Docker Root Dir"'])


def install_docker():
    os_info = get_os_info()
    os_name = os_info.get('NAME', '')

    if 'Ubuntu' in os_name:
        print("Running on Ubuntu")
        install_docker_ubuntu()
    elif 'Rocky' in os_name:
        print("Running on Rocky Linux")
        install_docker_rocky()
    else:
        print(f"Running on an unsupported OS: {os_name}")
        return


def main():
    # parser = argparse.ArgumentParser(description='System setup for an MDDB node.')
    install_docker()


if __name__ == '__main__':
    main()
