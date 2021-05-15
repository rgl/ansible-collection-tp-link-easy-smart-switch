# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

# hack to make this file directly executable as python3 switch.py.
if not __package__:
    import os.path
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(parent_directory)
    import sys
    sys.path.insert(0, os.path.dirname(parent_directory))

import logging
from .switch_take_ownership_client import SmrtSwitchTakeOwnershipClient

logger = logging.getLogger(__name__)


class SmrtSwitchTakeOwnership(object):

    def __init__(self, switch_client):
        self._client = switch_client

    def take_ownership(self, dry_run):
        desired_config = {
            'dhcp': False,
            'ip_addr': self._client._switch_ip_address,
            'ip_mask': self._client._host_ip_mask,
            'gateway': self._client._host_ip_address,
        }
        actual_config = self._client.get_config()
        changed = False
        if actual_config['dhcp'] != desired_config['dhcp']:
            changed = True
        if actual_config['ip_addr'] != desired_config['ip_addr']:
            changed = True
        if actual_config['ip_mask'] != desired_config['ip_mask']:
            changed = True
        if actual_config['gateway'] != desired_config['gateway']:
            changed = True
        if changed:
            logger.debug('%staking ownership', 'dry run: ' if dry_run else '')
            if not dry_run:
                self._client.set_config(desired_config)
        return changed


if __name__ == '__main__':
    import os.path
    import yaml

    logging.basicConfig(level=logging.DEBUG)

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/../../example-inventory.yml', 'r') as f:
        example_inventory = yaml.safe_load(f)
    smrt_switch_ip_address = list(example_inventory['all']['children']['smrt_switches']['hosts'].keys())[0]
    smrt_switch_mac_address = example_inventory['all']['children']['smrt_switches']['hosts'][smrt_switch_ip_address]['smrt_switch_mac_address']
    smrt_username = example_inventory['all']['vars']['smrt_username']
    smrt_password = example_inventory['all']['vars']['smrt_password']

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/../../example-take-ownership-playbook.yml', 'r') as f:
        example_playbook = yaml.safe_load(f)
    module_config = example_playbook[0]['tasks'][0]['rgl.tp_link_easy_smart_switch.smrt_take_ownership']

    switch = SmrtSwitchTakeOwnership(
        SmrtSwitchTakeOwnershipClient(
            smrt_switch_ip_address,
            smrt_switch_mac_address,
            smrt_username,
            smrt_password))
    changed = switch.take_ownership(True)

    logger.debug('settings changed? %s', changed)
