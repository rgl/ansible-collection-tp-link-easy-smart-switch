# Ansible Collection - rgl.tp_link_easy_smart_switch

**NB** This is an experimental collection.

This collection configures the [TP-Link Easy Smart switches](https://www.tp-link.com/en/business-networking/easy-smart-switch/).

This was only tested with the [TL-SG108E switch](https://www.tp-link.com/en/business-networking/easy-smart-switch/tl-sg108e/).

The switch is managed by sending commands to the UDP `255.255.255.255:29808` broadcast endpoint (and the switch replies to the `255.255.255.255:29809` endpoint).

**NB** This line of switches is somewhat insecure as, at least, its configuration protocol (UDP port 29808 and TCP port 80) uses cleartext messages. For more information see [How I can gain control of your TP-LINK home switch](https://www.pentestpartners.com/security-blog/how-i-can-gain-control-of-your-tp-link-home-switch/) and [Information disclosure vulnerability in TP-Link Easy Smart switches](https://www.chrisdcmoore.co.uk/post/tplink-easy-smart-switch-vulnerabilities/).

**NB** This line of switches also implements the [Realtek Remote Control Protocol (RRCP)](https://en.wikipedia.org/wiki/Realtek_Remote_Control_Protocol).

## Usage

See the [example-playbook.yml](example-playbook.yml) playbook and [example-inventory.yml](example-inventory.yml) inventory for an example usage and host requirements.

## TL-SG108E Switch Reset Procedure

While the switch is powered on:

1. Remove all cables (except your computer) from the switch ports.
4. Hold the switch Reset pin for 10 seconds and wait for it reset (blink all ports lights).
5. Add the `192.168.0.2` IP address to your computer, e.g.: `sudo ip addr add 192.168.0.2/24 dev enp3s0`.
6. Access http://192.168.0.1 and configure it as described in [example-playbook.yml](example-playbook.yml).
7. Remove the added IP address from your computer, e.g.: `sudo ip addr del 192.168.0.2/24 dev enp3s0`.

You can also reset it from the Web UI at:

* System
  * System Tools
    * System Reset

## Wireshark Filters

| Display filter                  | Capture filter                          | Description                     |
|---------------------------------|-----------------------------------------|---------------------------------|
| `eth.src[0:3] == 50:d4:f7`      | `ether[6:4] & 0xffffff00 == 0x50d4f700` | From TP-Link vendor             |
| `eth.dst[0:3] == 50:d4:f7`      | `ether[0:4] & 0xffffff00 == 0x50d4f700` | To TP-Link vendor               |
| `eth.addr[0:3] == 50:d4:f7`     | do an `and` of the previous two lines   | From or To TP-Link vendor       |
| `eth.addr == 50:d4:f7:22:22:22` | `ether host 50:d4:f7:22:22:22`          | Specific MAC address            |
| `vlan`                          | `vlan`                                  | All VLANs                       |
| `vlan.id == 2`                  | `vlan 2`                                | Specific VLAN                   |

For more information see:

* [Wireshark Display Filters](https://gitlab.com/wireshark/wireshark/-/wikis/DisplayFilters).
* [Wireshark Capture Filters](https://gitlab.com/wireshark/wireshark/-/wikis/CaptureFilters).
* [pcap capture filters `pcap-filter(7)`](http://manpages.ubuntu.com/manpages/focal/man7/pcap-filter.7.html).

## Development

This collection is developed in a Ubuntu 20.04 host by following these instructions.

Install Ansible:

```bash
ansible_version='2.10.7'        # see https://pypi.org/project/ansible/
ansible_lint_version='4.3.7'    # see https://pypi.org/project/ansible-lint/
# see https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-with-pip
sudo apt-get install -y --no-install-recommends python3-pip python3-venv python3-cryptography python3-yaml
rm -rf .ansible-venv
python3 -m venv --system-site-packages .ansible-venv
source .ansible-venv/bin/activate
# NB this pip install will display several "error: invalid command 'bdist_wheel'"
#    messages, those can be ignored.
python3 -m pip install "ansible==$ansible_version" "ansible-base==$ansible_version" "ansible-lint==$ansible_lint_version"
ansible --version
ansible -m ping localhost
```

For historical purposes, this collection skeleton was [created with `ansible-galaxy collection init`](https://docs.ansible.com/ansible/2.10/dev_guide/developing_collections.html#creating-a-collection-skeleton) as:

```bash
ansible-galaxy collection init rgl.tp_link_easy_smart_switch
cd rgl.tp_link_easy_smart_switch
git init
```

Build and try the collection:

```bash
export ANSIBLE_COLLECTIONS_PATH="$PWD/.ansible-collections"
rm -f rgl-tp_link_easy_smart_switch-*.tar.gz
ansible-galaxy collection build --verbose
tar tf rgl-tp_link_easy_smart_switch-*.tar.gz
ansible-galaxy collection install --verbose --force rgl-tp_link_easy_smart_switch-*.tar.gz
ansible-inventory --list --yaml
ansible-lint example-playbook.yml
ansible-playbook example-playbook.yml --syntax-check
ansible-playbook example-playbook.yml --list-hosts
ansible-playbook example-playbook.yml --check -vvv
ansible-playbook example-playbook.yml -vvv
```

Publish the collection:

```bash
# NB get this API key/token from https://galaxy.ansible.com/me/preferences.
export ANSIBLE_GALAXY_SERVER_RELEASE_GALAXY_TOKEN='my-api-token'
# NB as of 2021-05-09 there is no way to delete a collection from
#    galaxy.ansible.com. once published, there is no going back.
#    see https://github.com/ansible/galaxy/issues/1977
ansible-galaxy collection publish --verbose -vvv ./rgl-tp_link_easy_smart_switch-*.tar.gz
```

## Reference

* [Ansible: Developing collections](https://docs.ansible.com/ansible/2.10/dev_guide/developing_collections.html).
* [Ansible: Working With Plugins](https://docs.ansible.com/ansible/2.10/plugins/plugins.html).
* [The Easy Smart Configuration Protocol (ESCP)](https://www.chrisdcmoore.co.uk/post/tplink-easy-smart-switch-vulnerabilities/#the-easy-smart-configuration-protocol-escp).
* smrt python library
  * [Forked smrt library by Philippe Chataignon](https://github.com/philippechataignon/smrt)
    * the [`plugins/module_utils`](plugins/module_utils) directory contains a
      slightly modified version of the `smrt` library from the [e545df10a0abf4c576b1aedf1b54a8d0faebf290](https://github.com/philippechataignon/smrt/tree/e545df10a0abf4c576b1aedf1b54a8d0faebf290) tree.
  * [Original smrt library by Philipp Klaus](https://github.com/pklaus/smrt/tree/master/smrt)
