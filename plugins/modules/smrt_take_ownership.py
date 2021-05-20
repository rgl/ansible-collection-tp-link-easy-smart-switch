#!/usr/bin/python
# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
module: smrt_take_ownership
author: Rui Lopes (@rgl)
short_description: Take ownership of a TP-Link Easy Smart Switch
description:
    - Take ownership of a factory reset switch.
    - "**You must factory reset the swith before using this. Check the README for more information.**"
notes:
    - This module supports the I(check_mode).
requirements:
    - netifaces
options:
    username:
        required: True
        description:
            - The switch username.
            - The default username (admin) will be renamed to this value.
        type: str
    password:
        required: True
        description:
            - The switch password.
            - The switch password will be set to this value.
        type: str
    switch_ip_address:
        required: True
        description:
            - The switch ip address.
            - The switch ip address will be set to this value.
            - The switch ip address must be in a network directly accessible from the host.
            - The switch network mask will be inferred from the host ip address.
            - The switch gateway will be set to the host ip address.
        type: str
    switch_mac_address:
        required: True
        description:
            - The switch mac address.
        type: str
'''

EXAMPLES = '''
# NB before using this make sure you have read the take ownership section
#    of the README.
- name: Take ownership of the TL-SG108E switch
  connection: local
  rgl.tp_link_easy_smart_switch.smrt_config:
    username: admin
    password: HeyH0Password
    switch_ip_address: 10.1.0.2
    switch_mac_address: 50:d4:f7:22:22:22
'''

RETURN = '''
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib


class SmrtTakeOwnership(AnsibleModule):
    def __init__(self):
        super(SmrtTakeOwnership, self).__init__(
            argument_spec=dict(
                username=dict(type='str', required=True),
                password=dict(type='str', required=True, no_log=True),
                switch_ip_address=dict(type='str', required=True),
                switch_mac_address=dict(type='str', required=True)),
            supports_check_mode=True)

    def main(self):
        try:
            from ..module_utils.switch_take_ownership import SmrtSwitchTakeOwnership
            from ..module_utils.switch_take_ownership_client import SmrtSwitchTakeOwnershipClient
        except ImportError as e:
            self.fail_json(msg=missing_required_lib(e.name), exception=traceback.format_exc())

        switch = SmrtSwitchTakeOwnership(
            SmrtSwitchTakeOwnershipClient(
                self.params['switch_ip_address'],
                self.params['switch_mac_address'],
                self.params['username'],
                self.params['password']))

        changed = switch.take_ownership(self.check_mode)

        self.exit_json(changed=changed, content=dict())


def main():
    module = SmrtTakeOwnership()
    module.main()


if __name__ == '__main__':
    main()
