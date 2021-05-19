# Ansible Collection - rgl.tp_link_easy_smart_switch

[![Build status](https://github.com/rgl/ansible-collection-tp-link-easy-smart-switch/workflows/Build/badge.svg)](https://github.com/rgl/ansible-collection-tp-link-easy-smart-switch/actions?query=workflow%3ABuild)

**NB** This is an experimental collection.

This collection configures the [TP-Link Easy Smart switches](https://www.tp-link.com/en/business-networking/easy-smart-switch/).

This was only tested with the [TL-SG108E switch](https://www.tp-link.com/en/business-networking/easy-smart-switch/tl-sg108e/).

The switch is managed by sending commands to the UDP `255.255.255.255:29808` broadcast endpoint (and the switch replies to the `255.255.255.255:29809` endpoint).

**NB** This line of switches is somewhat insecure as, at least, its configuration protocol (UDP port 29808 and TCP port 80) uses cleartext messages. For more information see [How I can gain control of your TP-LINK home switch](https://www.pentestpartners.com/security-blog/how-i-can-gain-control-of-your-tp-link-home-switch/) and [Information disclosure vulnerability in TP-Link Easy Smart switches](https://www.chrisdcmoore.co.uk/post/tplink-easy-smart-switch-vulnerabilities/).

**NB** This line of switches also implements the [Realtek Remote Control Protocol (RRCP)](https://en.wikipedia.org/wiki/Realtek_Remote_Control_Protocol).

## Usage

Install [this collection from Ansible Galaxy](https://galaxy.ansible.com/rgl/tp_link_easy_smart_switch) with:

```bash
ansible-galaxy collection install rgl.tp_link_easy_smart_switch
```

Install the required python libraries:

```bash
# install dependencies in ubuntu 20.04.
sudo apt-get install -y --no-install-recommends \
    python3-netifaces
```

[Take ownership](#take-ownership-procedure) of the switch.

**NB** Normally you only need to do this once.

Review the [example-playbook.yml](example-playbook.yml) playbook and the [example-inventory.yml](example-inventory.yml) inventory files.

Execute the playbook:

```bash
ansible-playbook example-playbook.yml --check --diff -vvv
ansible-playbook example-playbook.yml --diff -vvv
```

To build this collection from source code see the [Development section](#development).

## Take Ownership Procedure

This procedure resets the switch to the default factory settings and sets the
switch `admin` user password and static IP configuration.

Make sure your computer has an IP address in the switch final network and
another in the switch default `192.168.0.0/24` network.

**NB** The switch will use the 192.168.0.1 IP address when there is no DHCP
server in the network.

This procedure assumes the host has the following netplan configuration:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp3s0:
      link-local: []
      addresses:
        - 10.1.0.1/24
        - 192.168.0.254/24
  bridges:
    br-rpi:
      link-local: []
      addresses:
        - 10.3.0.1/24
      interfaces:
        - vlan.rpi
  vlans:
    vlan.wan:
      id: 2
      link: enp3s0
      link-local: []
      addresses:
        - 192.168.1.1/24
      gateway4: 192.168.1.254
      nameservers:
        addresses:
          # cloudflare+apnic public dns resolvers.
          # see https://en.wikipedia.org/wiki/1.1.1.1
          - "1.1.1.1"
          - "1.0.0.1"
          # google public dns resolvers.
          # see https://en.wikipedia.org/wiki/8.8.8.8
          #- "8.8.8.8"
          #- "8.8.4.4"
    vlan.rpi:
      id: 3
      link: enp3s0
      link-local: []
```

Ensure that these addresses (and mac addresses) are defined in your inventory and playbook.

As an example, ensure they are defined in:

* [example-inventory.yml](example-inventory.yml)
* [example-take-ownership-playbook.yml](example-take-ownership-playbook.yml)
* [example-playbook.yml](example-inventory.yml)

While the switch is powered on:

1. Remove all cables (except your computer) from the switch ports.
2. Hold the switch Reset pin for 10 seconds and wait for it to reboot (when it blinks all the ports lights).
3. Wait for the switch to boot (when your computer switch port light blinks again, it should be good to go).
4. Execute the take ownership playbook, e.g.:
   ```bash
   ansible-playbook example-take-ownership-playbook.yml
   ```

You are now ready to execute the regular (non take-ownership) playbooks.

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

Install the build environment:

```bash
./build-install.sh
```

For historical purposes, this collection skeleton was [created with `ansible-galaxy collection init`](https://docs.ansible.com/ansible/2.11/dev_guide/developing_collections.html#creating-a-collection-skeleton) as:

```bash
ansible-galaxy collection init rgl.tp_link_easy_smart_switch
cd rgl.tp_link_easy_smart_switch
git init
```

Build and install the collection:

```bash
./build.sh
```

Try the collection:

```bash
source build-env.sh
ansible-galaxy collection install -r example-playbook-requirements.yml
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

* [Ansible: Developing collections](https://docs.ansible.com/ansible/2.11/dev_guide/developing_collections.html).
* [Ansible: Working With Plugins](https://docs.ansible.com/ansible/2.11/plugins/plugins.html).
* [The Easy Smart Configuration Protocol (ESCP)](https://www.chrisdcmoore.co.uk/post/tplink-easy-smart-switch-vulnerabilities/#the-easy-smart-configuration-protocol-escp).
* smrt python library
  * [Forked smrt library by Philippe Chataignon](https://github.com/philippechataignon/smrt)
    * the [`plugins/module_utils`](plugins/module_utils) directory contains a
      slightly modified version of the `smrt` library from the [e545df10a0abf4c576b1aedf1b54a8d0faebf290](https://github.com/philippechataignon/smrt/tree/e545df10a0abf4c576b1aedf1b54a8d0faebf290) tree.
  * [Original smrt library by Philipp Klaus](https://github.com/pklaus/smrt/tree/master/smrt)
* IRC Channels on [Freenode](https://en.wikipedia.org/wiki/Freenode):
  * [#ansible](irc://irc.freenode.net/#ansible)
  * [#ansible-community](irc://irc.freenode.net/#ansible-community)
  * [#ansible-galaxy](irc://irc.freenode.net/#ansible-galaxy)
  * [#ansible-devel](irc://irc.freenode.net/#ansible-devel)
