# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

import struct
import netifaces
from ipaddress import ip_address
from ipaddress import ip_network
from .network import Network
from .protocol import Protocol


class SmrtSwitchTakeOwnershipClientInterface(object):

    def get_config(self):
        pass

    def set_config(self, config):
        pass


class SmrtSwitchTakeOwnershipClient(SmrtSwitchTakeOwnershipClientInterface):

    def __init__(self, switch_ip_address, switch_mac_address, username, password):
        self._username = username
        self._password = password
        self._switch_ip_address = switch_ip_address
        (self._host_ip_address, self._host_ip_mask, self._host_mac_address) = self.__get_host_address()
        interface = self.__get_default_host_interface()
        self._network = Network(interface, switch_mac_address)

    def __get_host_address(self):
        for interface in netifaces.interfaces():
            if interface == 'lo':
                continue
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET not in addresses:
                continue
            if netifaces.AF_LINK not in addresses:
                continue
            for inet in addresses[netifaces.AF_INET]:
                host_network = ip_network(f"{inet['addr']}/{inet['netmask']}", False)
                switch_network = ip_network(f"{self._switch_ip_address}/{inet['netmask']}", False)
                if host_network == switch_network:
                    host_ip_address = inet['addr']
                    host_ip_mask = inet['netmask']
                    host_mac_address = addresses[netifaces.AF_LINK][0]['addr']
                    return (host_ip_address, host_ip_mask, host_mac_address)
        raise Exception(f'could not find a host ip address in the same network as the switch {self._switch_ip_address}')

    def __get_default_host_interface(self):
        default_network = ip_network('192.168.0.0/24')
        for interface in netifaces.interfaces():
            if interface == 'lo':
                continue
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET not in addresses:
                continue
            if netifaces.AF_LINK not in addresses:
                continue
            for inet in addresses[netifaces.AF_INET]:
                network = ip_network(f"{inet['addr']}/{inet['netmask']}", False)
                if default_network == network:
                    default_host_ip_address = str(inet['addr'])
                    default_host_mac_address = addresses[netifaces.AF_LINK][0]['addr']
                    return interface
        raise Exception(f'could not find a host ip address in the default switch network {default_network}')

    def get_config(self):
        # NB this does not require authentication.
        # NB this returns something alike:
        #       (9, 'dhcp', False)
        #       (4, 'ip_addr', IPv4Address('10.1.0.2'))
        #       (5, 'ip_mask', IPv4Address('255.255.255.0'))
        #       (6, 'gateway', IPv4Address('10.1.0.1'))
        _header, payload = self._network.query(Protocol.GET, [(Protocol.get_id('dhcp'), b'')])
        result = {}
        for p in payload:
            if p[1] == 'dhcp':
                result['dhcp'] = p[2]
            if p[1] == 'ip_addr':
                result['ip_addr'] = str(p[2])   # p[2] is-a ipaddress.IPv4Address
            if p[1] == 'ip_mask':
                result['ip_mask'] = str(p[2])   # p[2] is-a ipaddress.IPv4Address
            if p[1] == 'gateway':
                result['gateway'] = str(p[2])   # p[2] is-a ipaddress.IPv4Address
        return result

    def set_config(self, config):
        default_username = 'admin'
        default_password = 'admin'
        # set the credentials.
        set_payload = [
            (Protocol.get_id('password'), default_password.encode('ascii') + b'\x00'),
            (Protocol.get_id('new_username'), self._username.encode('ascii') + b'\x00'),
            (Protocol.get_id('new_password'), self._password.encode('ascii') + b'\x00'),
        ]
        _header, _payload = self._network.set(
            default_username,
            default_password,
            set_payload)
        if _header['op_code'] != 4 or _header['error_code'] != 0:
            raise Exception(f"failed to modify the default switch credentials (error_code={_header['error_code']}). have you reset the switch configuration?")
        # set the ip configuration (using the new credentials).
        set_payload = [
            (Protocol.get_id('dhcp'), struct.pack('!?', config['dhcp'])),
            (Protocol.get_id('ip_addr'), ip_address(config['ip_addr']).packed),
            (Protocol.get_id('ip_mask'), ip_address(config['ip_mask']).packed),
            (Protocol.get_id('gateway'), ip_address(config['gateway']).packed),
        ]
        _header, _payload = self._network.set(
            self._username,
            self._password,
            set_payload)
        if _header['status_code'] != 0:
            raise Exception(f"failed set the ip configuration (error_code={_header['error_code']}). have you reset the switch configuration?")
