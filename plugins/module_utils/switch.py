# Copyright (c) 2021 Rui Lopes (ruilopes.com).
#
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

# hack to make this file directly executable as python3 switch.py.
if __package__ is None:
    import os.path
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(parent_directory)
    import sys
    sys.path.insert(0, os.path.dirname(parent_directory))

import logging
from .switch_client import SmrtSwitchClient

logger = logging.getLogger(__name__)


class SmrtSwitch(object):

    def __init__(self, switch_client):
        self._client = switch_client

    def get_config(self):
        ports = {}
        pvids = {p['port']: p['pvid'] for p in self._client.get_pvids()}
        for p in self._client.get_ports():
            port = p['port']
            ports[port] = {
                'port': port,
                'name': str(port),
                'pvid': pvids[port],
                'enabled': p['status'] == 1,
                '_data': p,
            }
        vlans = {}
        for v in self._client.get_vlans():
            vlan_id = v['vlan_id']
            tagged_ports = v['tagged_ports']
            member_ports = v['member_ports']
            vlans[vlan_id] = {
                'vlan_id': vlan_id,
                'name': v['name'],
                'tagged_ports': tagged_ports,
                'untagged_ports': sorted(set(member_ports) - set(tagged_ports)),
            }
        return {
            'ports': ports,
            'vlans': vlans,
        }

    def set_config(self, dry_run, desired_config):
        actual_config = self.get_config()
        return self._set_config_diff(
            dry_run,
            actual_config,
            desired_config,
            self._get_config_diff(actual_config, desired_config))

    def _get_config_diff(self, actual_config, desired_config):
        actual_ports = actual_config['ports']
        actual_vlans = actual_config['vlans']

        # index the ports by name and port number.
        ports = {p['name']: p for p in desired_config['ports'] if p.get('name')}
        ports.update({str(p['port']): p for p in desired_config['ports']})
        # also add undefined ports by port number, so we can refer them by
        # number in vlans too.
        for p in set(actual_ports.keys()) - set(ports.keys()):
            ports[str(p)] = {'port': p}

        # index the vlans by name and vlan id.
        vlans = {v['name']: v for v in desired_config['vlans'] if v.get('name')}
        vlans.update({v['vlan_id']: v for v in desired_config['vlans']})

        # TODO gracefully abort when any desired_config ports references unknown vlans pvid.
        # TODO gracefully abort when any desired_config vlans does not have vlan 1.

        # get the normalized desired vlans from the module parameters.
        # NB tagged_ports and untagged_ports are normalized into port numbers.
        #    (port names are normalized into port numbers).
        desired_vlans = {
            v['vlan_id']: {
                'vlan_id': v['vlan_id'],
                'name': v['name'],
                'tagged_ports': [ports[p]['port'] for p in v.get('tagged_ports') or []],
                'untagged_ports': [ports[p]['port'] for p in v.get('untagged_ports') or []],
            }
            for v in desired_config['vlans']
        }

        # get the normalized desired ports from the module parameters.
        # NB pvid is normalized into a vlan id.
        # NB when the user did not specify the pvid, we will use the vlan id
        #    from the firt vlan that has the port as an untagged port or 1.
        deduced_pvids = {}
        for vlan_id, vlan in desired_vlans.items():
            for port in vlan['untagged_ports']:
                if port not in deduced_pvids:
                    deduced_pvids[port] = vlan_id
        desired_ports = {
            p['port']: {
                'port': p['port'],
                'name': p.get('name'),
                'pvid': p.get('pvid') and vlans[p['pvid']]['vlan_id'] or deduced_pvids.get(p['port'], 1),
                'enabled': p.get('enabled', True),
            }
            for p in desired_config['ports']
        }

        # make sure undefined ports will be disabled and put in vlan 1 as
        # untagged ports.
        undefined_ports = set(actual_ports.keys()) - set(desired_ports.keys())
        for port in undefined_ports:
            desired_ports[port] = {
                'port': port,
                'name': str(port),
                'pvid': 1,
                'enabled': False,
            }
            desired_vlans[1]['untagged_ports'].append(port)

        # make sure ports that are not explicitly added in any vlans are
        # disabled and put in vlan 1 as untagged ports.
        ports_with_vlan = set()
        for vlan in desired_vlans.values():
            ports_with_vlan.update(vlan['tagged_ports'])
            ports_with_vlan.update(vlan['untagged_ports'])
        ports_without_vlan = set(desired_ports.keys()) - ports_with_vlan
        for port in ports_without_vlan:
            desired_ports[port]['enabled'] = False
            desired_ports[port]['pvid'] = 1
            desired_vlans[1]['untagged_ports'].append(port)

        # compute the diff between the actual and desired ports state.
        ports_diff = {}
        # compute which ports need to be added or modified.
        for port, desired_port in desired_ports.items():
            desired_enabled = desired_port['enabled']
            desired_pvid = desired_port['pvid']
            actual_port = actual_ports.get(port)
            if actual_port:
                actual_enabled = actual_port['enabled']
                actual_pvid = actual_port['pvid']
            else:
                actual_enabled = None
                actual_pvid = None
            ports_diff[port] = {
                'port': port,
                'enabled': {
                    'equal': desired_enabled if desired_enabled == actual_enabled else None,
                    'add': desired_enabled if desired_enabled != actual_enabled else None,
                    'remove': actual_enabled if actual_enabled != desired_enabled else None,
                },
                'pvid': {
                    'equal': desired_pvid if desired_pvid == actual_pvid else None,
                    'add': desired_pvid if desired_pvid != actual_pvid else None,
                    'remove': actual_pvid if actual_pvid != desired_pvid else None,
                },
            }
        # compute which ports need to be removed.
        # NB we cannot actually remove them. instead they are disabled
        #    and put in pvid 1.
        for port, actual_port in actual_ports.items():
            if port in ports_diff:
                continue
            desired_enabled = False
            desired_pvid = 1
            actual_enabled = actual_port['enabled']
            actual_pvid = actual_port['pvid']
            ports_diff[port] = {
                'port': port,
                'enabled': {
                    'equal': desired_enabled if desired_enabled == actual_enabled else None,
                    'add': desired_enabled if desired_enabled != actual_enabled else None,
                    'remove': actual_enabled if actual_enabled != desired_enabled else None,
                },
                'pvid': {
                    'equal': desired_pvid if desired_pvid == actual_pvid else None,
                    'add': desired_pvid if desired_pvid != actual_pvid else None,
                    'remove': actual_pvid if actual_pvid != desired_pvid else None,
                },
            }

        # compute the diff between the actual and desired vlans state.
        vlans_diff = {}
        # compute which vlans need to be added or modified.
        for vlan_id, desired_vlan in desired_vlans.items():
            desired_name = desired_vlan['name']
            desired_tagged_ports = set(desired_vlan['tagged_ports'])
            desired_untagged_ports = set(desired_vlan['untagged_ports'])
            actual_vlan = actual_vlans.get(vlan_id)
            if actual_vlan:
                actual_name = actual_vlan['name']
                actual_tagged_ports = set(actual_vlan['tagged_ports'])
                actual_untagged_ports = set(actual_vlan['untagged_ports'])
            else:
                actual_name = None
                actual_tagged_ports = set()
                actual_untagged_ports = set()
            vlans_diff[vlan_id] = {
                'vlan_id': vlan_id,
                'name': {
                    'equal': desired_name if desired_name == actual_name else None,
                    'add': desired_name if desired_name != actual_name else None,
                    'remove': actual_name if actual_name != desired_name else None,
                },
                'tagged_ports': {
                    'equal': sorted(desired_tagged_ports.intersection(actual_tagged_ports)) or None,
                    'add': sorted(desired_tagged_ports - actual_tagged_ports) or None,
                    'remove': sorted(actual_tagged_ports - desired_tagged_ports) or None,
                },
                'untagged_ports': {
                    'equal': sorted(desired_untagged_ports.intersection(actual_untagged_ports)) or None,
                    'add': sorted(desired_untagged_ports - actual_untagged_ports) or None,
                    'remove': sorted(actual_untagged_ports - desired_untagged_ports) or None,
                },
            }
        # compute which vlans need to be removed.
        for vlan_id, actual_vlan in actual_vlans.items():
            if vlan_id in vlans_diff:
                continue
            vlans_diff[vlan_id] = {
                'vlan_id': vlan_id,
                'name': {
                    'equal': None,
                    'add': None,
                    'remove': actual_vlan['name'],
                },
                'tagged_ports': {
                    'equal': None,
                    'add': None,
                    'remove': actual_vlan['tagged_ports'],
                },
                'untagged_ports': {
                    'equal': None,
                    'add': None,
                    'remove': actual_vlan['untagged_ports'],
                },
            }

        return {
            'ports': ports_diff,
            'vlans': vlans_diff,
        }

    def _set_config_diff(self, dry_run, actual_config, desired_config, config_diff):
        # create the desired ports configuration changes.
        ports = []
        for port, d in config_diff['ports'].items():
            if d['enabled']['add'] is not None:
                port_data = actual_config['ports'][port]['_data']
                ports.append({
                    'port': port,
                    'status': 1 if d['enabled']['add'] else 0,
                    'lag': port_data['lag'],
                    'speed': port_data['speed'],
                    'flow_control': port_data['flow_control'],
                })

        # create the desired ports pvids configuration changes.
        pvids = []
        for port, d in config_diff['ports'].items():
            if d['pvid']['add'] is not None:
                pvids.append({
                    'port': port,
                    'pvid': d['pvid']['add'],
                })

        # create the desired vlans configuration changes.
        # NB because a port must be in at least one vlan (and a port pvid must
        #    exist), we have to configure the vlans in three steps:
        #       1. add the ports to new vlans
        #       2. set the pvids
        #       3. set the ports vlans (this will remove from old vlans).
        add_vlans = []
        for vlan_id, d in config_diff['vlans'].items():
            changed = d['name']['add'] is not None
            changed = changed or d['tagged_ports']['add'] is not None
            changed = changed or d['untagged_ports']['add'] is not None
            if not changed:
                continue
            tagged_ports = set(d['tagged_ports']['add'] or []) | set(d['tagged_ports']['equal'] or []) | set(d['tagged_ports']['remove'] or [])
            untagged_ports = set(d['untagged_ports']['add'] or []) | set(d['untagged_ports']['equal'] or []) | set(d['untagged_ports']['remove'] or [])
            member_ports = tagged_ports | untagged_ports
            add_vlans.append({
                'vlan_id': vlan_id,
                'name': d['name']['add'] or d['name']['equal'],
                'member_ports': sorted(member_ports),
                'tagged_ports': sorted(tagged_ports)})
        vlans = []
        for vlan_id, d in config_diff['vlans'].items():
            changed = d['name']['add'] is not None or d['name']['remove'] is not None
            changed = changed or d['tagged_ports']['add'] is not None or d['tagged_ports']['remove'] is not None
            changed = changed or d['untagged_ports']['add'] is not None or d['untagged_ports']['remove'] is not None
            if not changed:
                continue
            tagged_ports = set(d['tagged_ports']['add'] or []) | set(d['tagged_ports']['equal'] or [])
            untagged_ports = set(d['untagged_ports']['add'] or []) | set(d['untagged_ports']['equal'] or [])
            member_ports = tagged_ports | untagged_ports
            vlans.append({
                'vlan_id': vlan_id,
                'name': d['name']['add'] or d['name']['equal'],
                'member_ports': sorted(member_ports),
                'tagged_ports': sorted(tagged_ports)})

        changed = False

        if ports:
            for p in ports:
                logger.debug('%smodifying port %s', 'dry run: ' if dry_run else '', p['port'])
            if not dry_run:
                self._client.set_ports(ports)
            changed = True

        if add_vlans:
            for v in add_vlans:
                logger.debug('%sadding new ports to vlan %s %s', 'dry run: ' if dry_run else '', v['vlan_id'], v['name'])
            if not dry_run:
                self._client.set_vlans(add_vlans)
            changed = True

        if pvids:
            for p in pvids:
                logger.debug('%smodifying pvid of port %s to %s', 'dry run: ' if dry_run else '', p['port'], p['pvid'])
            if not dry_run:
                self._client.set_pvids(pvids)
            changed = True

        if vlans:
            for v in add_vlans:
                logger.debug('%smodifying vlan %s %s', 'dry run: ' if dry_run else '', v['vlan_id'], v['name'])
            if not dry_run:
                self._client.set_vlans(vlans)
            changed = True

        return changed


if __name__ == '__main__':
    import os.path
    import yaml

    logging.basicConfig(level=logging.DEBUG)

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/../../example-inventory.yml', 'r') as f:
        example_inventory = yaml.safe_load(f)
    smrt_host_ip_address = example_inventory['all']['vars']['smrt_host_ip_address']
    smrt_host_mac_address = example_inventory['all']['vars']['smrt_host_mac_address']
    smrt_switch_mac_address = example_inventory['all']['children']['smrt_switches']['hosts']['10.1.0.2']['smrt_switch_mac_address']
    smrt_username = example_inventory['all']['vars']['smrt_host_mac_address']
    smrt_password = example_inventory['all']['vars']['smrt_password']

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/../../example-playbook.yml', 'r') as f:
        example_playbook = yaml.safe_load(f)
    module_config = example_playbook[0]['tasks'][0]['rgl.tp_link_easy_smart_switch.smrt_config']
    config = {
        'ports': module_config['ports'],
        'vlans': module_config['vlans'],
    }

    switch = SmrtSwitch(
        SmrtSwitchClient(
            smrt_host_ip_address,
            smrt_host_mac_address,
            smrt_switch_mac_address,
            smrt_username,
            smrt_password))
    changed = switch.set_config(True, config)

    logger.debug('settings changed? %s', changed)
