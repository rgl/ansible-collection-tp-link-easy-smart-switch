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
notes:
   - This module supports the I(check_mode) and I(diff_mode).
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
    host_interface:
        required: True
        description:
            - The host interface.
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
# NB this assumes that you have taken ownership of the switch as described
#    in the README.
- name: Configure the TL-SG108E switch
  connection: local
  rgl.tp_link_easy_smart_switch.smrt_config:
    username: admin
    password: admin
    host_interface: enp2s0f0
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
                host_interface=dict(type='str', required=True),
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
                self.params['host_interface'],
                self.params['switch_mac_address'],
                self.params['username'],
                self.params['password']))

        result = switch.set_config(self.check_mode, {
            'ports': self.params['ports'],
            'vlans': self.params['vlans'],
        })

        diff = None

        if self._diff:
            diff = {
                'prepared': get_highlighted_diff(result['diff']),
            }

        self.exit_json(changed=result['changed'], content=dict(), diff=diff)


# NB this came from https://github.com/ansible/ansible/blob/v2.11.0/lib/ansible/constants.py#L89-L101
COLOR_CODES = {
    'black': u'0;30', 'bright gray': u'0;37',
    'blue': u'0;34', 'white': u'1;37',
    'green': u'0;32', 'bright blue': u'1;34',
    'cyan': u'0;36', 'bright green': u'1;32',
    'red': u'0;31', 'bright cyan': u'1;36',
    'purple': u'0;35', 'bright red': u'1;31',
    'yellow': u'0;33', 'bright purple': u'1;35',
    'dark gray': u'1;30', 'bright yellow': u'1;33',
    'magenta': u'0;35', 'bright magenta': u'1;35',
    'normal': u'0',
}
COLOR_DIFF_ADD = 'green'
COLOR_DIFF_REMOVE = 'red'
COLOR_DIFF_LINES = 'cyan'


# NB this is a simplified version of https://github.com/ansible/ansible/blob/v2.11.0/lib/ansible/utils/color.py#L73-L93
# see https://github.com/ansible/ansible/issues/74793
def stringc(text, color):
    color_code = COLOR_CODES[color]
    fmt = u"\033[%sm%s\033[0m"
    return u"\n".join([fmt % (color_code, t) for t in text.split(u'\n')])


# NB this came from https://github.com/ansible/ansible/blob/v2.11.0/lib/ansible/plugins/callback/__init__.py#L220-L227
# see https://github.com/ansible/ansible/issues/74793
def get_highlighted_diff(diff):
    lines = []
    for line in diff.splitlines(True):
        if line.startswith('+'):
            line = stringc(line, COLOR_DIFF_ADD)
        elif line.startswith('-'):
            line = stringc(line, COLOR_DIFF_REMOVE)
        elif line.startswith('@@'):
            line = stringc(line, COLOR_DIFF_LINES)
        lines.append(line)
    return ''.join(lines)


def main():
    module = SmrtConfig()
    module.main()


if __name__ == '__main__':
    main()
