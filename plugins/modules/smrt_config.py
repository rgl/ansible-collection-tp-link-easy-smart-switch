#!/usr/bin/python
# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: smrt_config
author: Rui Lopes (@rgl)
short_description: Configure a TP-Link Easy Smart Switch
description:
    - Configure a TP-Link Easy Smart Switch ports and vlans.
options:
    username:
        required: True
        description:
            - The switch username.
        type: str
    password:
        required: True
        description:
            - The switch password.
        type: str
    host_ip_address:
        required: True
        description:
            - The host ip address.
        type: str
    host_mac_address:
        required: True
        description:
            - The host mac address.
        type: str
    switch_mac_address:
        required: True
        description:
            - The switch mac address.
        type: str
    ports:
        required: True
        description:
            - The switch ports configuration.
            - Any port not configured here will be disabled and put in vlan 1.
        type: list
        elements: dict
        suboptions:
            port:
                required: True
                description:
                    - The port number.
                type: int
            pvid:
                description:
                    - The Port Vlan ID (PVID) or the VLAN name.
                    - When the switch receives an untagged frame from this port, it will tag it with this PVID.
                type: str
            name:
                description:
                    - The port name.
                    - This can be used in the vlans options to logically refer to a port by its logical name instead of its number.
                type: str
            enabled:
                description:
                    - Whether this port should be enabled.
                    - Defaults to True.
                type: bool
                default: True
    vlans:
        required: True
        description:
            - The switch vlans configuration.
            - Any port not configured here will be put in vlan 1.
        type: list
        elements: dict
        suboptions:
            vlan_id:
                required: True
                description:
                    - The VLAN ID (1-4094).
                type: int
            name:
                required: True
                description:
                    - The VLAN name.
                type: str
            tagged_ports:
                description:
                    - This VLAN frames are forwarded to these ports as tagged frames.
                    - You can use the port number or the port name.
                type: list
                elements: str
            untagged_ports:
                description:
                    - This VLAN frames are forwarded to these ports as untagged frames.
                    - You can use the port number or the port name.
                type: list
                elements: str
'''

EXAMPLES = '''
# NB before using this you MUST manually reset your switch and then set:
#     * System
#       * User Account
#         * New Username:     admin
#         * Old Password:     admin
#         * New Password:     admin
#         * Confirm Password: admin
#       * IP Setting
#         * DHCP Setting:    Disable
#         * IP address:      10.1.0.2
#         * Subnet Mask:     255.255.255.0
#         * Default Gateway: 10.1.0.1
#    AND your management computer should be configured as:
#       network:
#       version: 2
#       renderer: networkd
#       ethernets:
#         enp3s0:
#           link-local: []
#           addresses:
#             - 10.1.0.1/24
#       bridges:
#         br-rpi:
#           link-local: []
#           addresses:
#             - 10.3.0.1/24
#           interfaces:
#             - vlan.rpi
#       vlans:
#         vlan.wan:
#           id: 2
#           link: enp3s0
#           link-local: []
#           addresses:
#             - 192.168.1.1/24
#           gateway4: 192.168.1.254
#           nameservers:
#             addresses:
#               - 8.8.8.8
#               - 8.8.4.4
#               - 1.1.1.1
#         vlan.rpi:
#           id: 3
#           link: enp3s0
#           link-local: []
- name: Configure the TL-SG108E switch
  connection: local
  rgl.tp_link_easy_smart_switch.smrt_config:
    username: admin
    password: admin
    host_ip_address: 10.1.0.1
    host_mac_address: 08:60:6e:11:11:11
    switch_mac_address: 50:d4:f7:22:22:22
    # NB undefined ports will be disabled and put in vlan 1 as untagged
    #    ports.
    # NB ports that are not explicitly added in vlans will be disabled
    #    and put in vlan 1 as untagged ports.
    # NB ports without explicit pvid will be deduced from the vlans (use
    #    the first vlan that has the port as an untagged port).
    ports:
      - port: 1
        name: isp
      - port: 2
        name: desktop
      - port: 5
        name: rpi1
      - port: 6
        name: rpi2
      - port: 7
        name: rpi3
      - port: 8
        name: rpi4
    vlans:
      # NB do not remove your management computer (in this example, its in
      #    the desktop port) from vlan 1 because that is the only vlan
      #    that can manage the switch.
      - vlan_id: 1
        name: management
        untagged_ports:
          - desktop
      - vlan_id: 2
        name: wan
        tagged_ports:
          - desktop
        untagged_ports:
          - isp
      - vlan_id: 3
        name: rpi
        tagged_ports:
          - desktop
        untagged_ports:
          - rpi1
          - rpi2
          - rpi3
          - rpi4
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.switch import SmrtSwitch
from ..module_utils.switch_client import SmrtSwitchClient


class SmrtConfig(AnsibleModule):
    def __init__(self):
        super(SmrtConfig, self).__init__(
            argument_spec=dict(
                username=dict(type='str', required=True),
                password=dict(type='str', required=True, no_log=True),
                host_ip_address=dict(type='str', required=True),
                host_mac_address=dict(type='str', required=True),
                switch_mac_address=dict(type='str', required=True),
                ports=dict(type='list', elements='dict', required=True, options=dict(
                    port=dict(type='int', required=True),
                    pvid=dict(type='str'),
                    name=dict(type='str'),
                    enabled=dict(type='bool', default=True),
                )),
                vlans=dict(type='list', elements='dict', required=True, options=dict(
                    vlan_id=dict(type='int', required=True),
                    name=dict(type='str', required=True),
                    tagged_ports=dict(type='list', elements='str'),
                    untagged_ports=dict(type='list', elements='str'),
                ))),
            supports_check_mode=True)

    def main(self):
        switch = SmrtSwitch(
            SmrtSwitchClient(
                self.params['host_ip_address'],
                self.params['host_mac_address'],
                self.params['switch_mac_address'],
                self.params['username'],
                self.params['password']))

        changed = switch.set_config(self.check_mode, {
            'ports': self.params['ports'],
            'vlans': self.params['vlans'],
        })

        self.exit_json(changed=changed, content=dict())


def main():
    module = SmrtConfig()
    module.main()


if __name__ == '__main__':
    main()
