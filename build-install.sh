#!/bin/bash
set -euxo pipefail

# install ansible dependencies from system packages.
# see https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-with-pip
sudo apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    python3-cryptography \
    python3-yaml \
    python3-netifaces \
    pylint

# (re)create the venv.
rm -rf .ansible-venv
python3 -m venv --system-site-packages .ansible-venv
source .ansible-venv/bin/activate

# ansible pip dependencies.
# NB this pip install will display several "error: invalid command 'bdist_wheel'"
#    messages, those can be ignored.
python3 -m pip install -r requirements.txt
# ansible-test pip dependencies.
python3 -m pip install -r requirements-test.txt

# try it.
ansible --version
ansible -m ping localhost
