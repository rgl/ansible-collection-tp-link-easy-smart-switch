# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

from .network import Network
from .protocol import Protocol
from .binary import mac_to_bytes


def ports_to_byte(ports):
    b = 0
    for n in ports:
        b |= 1 << (n - 1)
    return b


class SmrtSwitchClientInterface(object):

    def get_ports(self):
        pass

    def set_ports(self, ports):
        pass

    def get_pvids(self):
        pass

    def set_pvids(self, pvids):
        pass

    def get_vlans(self):
        pass

    def set_vlans(self, vlans):
        pass


class SmrtSwitchClient(SmrtSwitchClientInterface):

    def __init__(self, host_ip_address, host_mac_address, switch_mac_address, username, password):
        self._username = username
        self._password = password
        self._network = Network(host_ip_address, host_mac_address, switch_mac_address)
        self._network.login(username, password)

    def get_ports(self):
        # get the actual ports from the switch.
        _header, payload = self._network.query(Protocol.GET, [(Protocol.get_id('ports'), b'')])
        # payload is an array of tuples (property_id, property_name, ...depend on property_id...):
        #   (4096, 'ports', enabled) # e.g. (4096, 'ports', '01:01:00:01:06:00:00')
        #                                                    ^^ ^^ ^^ ^^ ^^ ^^ ^^
        #                                                    |  |  |  |  |  |  |
        #                                                 port  |  |  |  |  |  actual flow control
        #                                                  status  |  |  |  flow control
        #                                          00 == Disabled  |  |  |  00 == Off
        #                                           01 == Enabled  |  |  |  01 == On
        #                                                        LAG  |  actual speed
        #                                                             speed
        #                                                             01 == Auto
        #                                                             02 == 10MH
        #                                                             03 == 10MF
        #                                                             04 == 100MH
        #                                                             05 == 100MF
        #                                                             06 == 1000MF
        for p in payload:
            if p[1] == 'ports':
                data = p[2].split(':')
                yield {
                    'port': int(data[0], 16),
                    'status': int(data[1], 16),
                    'lag': int(data[2], 16),
                    'speed': int(data[3], 16),
                    'actual_speed': int(data[4], 16),
                    'flow_control': int(data[5], 16),
                    'actual_flow_control': int(data[6], 16),
                }

    def set_ports(self, ports):
        set_payload = []
        for p in ports:
            set_payload.append((
                Protocol.get_id('ports'),
                mac_to_bytes(
                    '%02x:%02x:%02x:%02x:00:%02x:00' % (
                        p['port'],
                        p['status'],
                        p['lag'],
                        p['speed'],
                        p['flow_control']))))
        _header, _payload = self._network.set(
            self._username,
            self._password,
            set_payload)
        # TODO verify the returned payload.

    def get_pvids(self):
        # get the actual pvids from the switch and set them in actual_ports.
        _header, payload = self._network.query(Protocol.GET, [(Protocol.get_id('pvid'), b'')])
        # payload is an array of tuples (property_id, property_name, ...depend on property_id...):
        #   (8706, 'pvid', (port, pvid)) # e.g. (8706, 'pvid', (1, 1))
        #   (8707, 'vlan_filler', vlan_filler) # e.g. (8707, 'vlan_filler', ' ')
        for p in payload:
            if p[1] == 'pvid':
                yield {
                    'port': int(p[2][0]),
                    'pvid': int(p[2][1]),
                }

    def set_pvids(self, pvids):
        set_payload = []
        for v in pvids:
            set_payload.append((
                Protocol.get_id('pvid'),
                Protocol.set_pvid(
                    v['pvid'],
                    v['port'])))
        _header, _payload = self._network.set(
            self._username,
            self._password,
            set_payload)
        # TODO verify the returned payload. it returns the settings after our change, we should verify if they match our expectation.

    def get_vlans(self):
        # get the actual vlans from the switch.
        _header, payload = self._network.query(Protocol.GET, [(Protocol.get_id('vlan'), b'')])
        # payload is an array of tuples (property_id, property_name, ...depend on property_id...):
        #   (8704, 'vlan_enabled', enabled) # e.g. (8704, 'vlan_enabled', '01')
        #   (8705, 'vlan', (vlan_id, member_ports, tagged_ports, vlan_name)) # e.g. (8705, 'vlan', (1, '1,2,4', '', 'Default'))
        for p in payload:
            if p[1] == 'vlan':
                yield {
                    'vlan_id': int(p[2][0]),
                    'name': p[2][3],
                    'member_ports': [int(s) for s in p[2][1].split(',') if s],
                    'tagged_ports': [int(s) for s in p[2][2].split(',') if s],
                }

    def set_vlans(self, vlans):
        # NB we have to set each vlan individually, because there's a bug
        #    somewhere in the firmware, that for some reason, the vlan name
        #    is messed up when we try to set several vlans at once.
        for v in vlans:
            set_payload = []
            set_payload.append((
                Protocol.get_id('vlan'),
                Protocol.set_vlan(
                    v['vlan_id'],
                    ports_to_byte(v['member_ports']),
                    ports_to_byte(v['tagged_ports']),
                    v['name'] or '')))
            _header, _payload = self._network.set(
                self._username,
                self._password,
                set_payload)
            # TODO verify the returned payload.
