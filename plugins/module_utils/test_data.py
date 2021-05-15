# Copyright (c) 2021 Rui Lopes (ruilopes.com).
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

# this is an example on how to decode the captured traffic from the UDP data.

# hack to make this file directly executable as python3 switch.py.
if not __package__:
    import os.path
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(parent_directory)
    import sys
    sys.path.insert(0, os.path.dirname(parent_directory))

from .protocol import Protocol


def decode(hex):
    return Protocol.analyze(Protocol.decode(bytes.fromhex(hex)))


# request: get token (get_token_id).
header, payload = decode('''
    5d753ad08a821613a93f0640dc1e7f9f422ba2f5d787aeed508f731dc202909a
    521281c6d8d52b36''')
# response: get token response.
header, payload = decode('''
    5d763ad08a821613a93f0640dc1e7f9f422ba2f5d78baeed508f314ac202909a
    a4ec81c6''')

# request: login (username, password).
header, payload = decode('''
    5d773ad08a821613a93f0640dc1e7f9e422ba2f5d792aeed508f314ac202909a
    591381c1464e465f27eb40b5a640635438023f5d103cff4538eb890873''')
# response: login.
header, payload = decode('''
    5d703ad08a821613a93f0640dc1e7f9e422ba2f5d78baeed508f314ac202909a
    a4ec81c6''')

# request: number of ports (num_ports).
header, payload = decode('''
    5d753ad08a821613a93f0640dc1e7f99422ba2f5d787aeed508f314ac202909a
    5b1981c6d8d52b36''')
# response: number of ports (num_ports).
header, payload = decode('''
    5d763ad08a821613a93f0640dc1e7f99422ba2f5d786aeed508f314ac202909a
    5b1981c72fd5d43649''')

# request: hostname (hostname).
header, payload = decode('''
    5d753ad08a821613a93f0640dc1e7f98422ba2f5d787aeed508f314ac202909a
    5b1181c6d8d52b36''')
# response: hostname (type, hostname, mac, firmware, hardware, dhcp, ip_addr, ip_mask, gateway, v4)
header, payload = decode('''
    5d763ad08a821613a93f0640dc1e7f98422ba2f5d703aeed508f314ac202909a
    5b1281cc736606650ee8708fe140692659647d184c7aae410f2c4f3842d3c1af
    6118ca8482d568b38f254a50f3d616160b86eba4c123dff0a8b3bfd8c9e7902d
    3690294a8182a0ed0ac6b79ca8aeb13969d79ec31aa0df9ea6fe5de4d1f3cd11
    a4d9bb7195502e658af7af2b9110abecdccfb1f043f17c83498fb7f76b06a6e8
    1a2bdfae950de25a8d5f92a5''')

# request: set credentials (username, password, password, new_username, new_password).
header, payload = decode('''
    5d773ad08a821613a93f0640dc1e7f93422ba2f5d7cdaeed508f731dc202909a
    591381c1464e465f27eb40b5a640605438023f5d103cff773a167601038081e8
    23418fd8bbe769b38b44286d4e4f18b0a885ecaeae7382b3f1ecedfe8e8e03b6
    16a2''')
# response: set credentials (when successfull returns header op_code 4; empty payload).
header, payload = decode('''
    5d703ad08a821613a93f0640dc1e7f81422ba2f5d78baeed508f5491c202909a
    a4ec81c6''')
