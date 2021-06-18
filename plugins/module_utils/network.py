import socket, random, logging, netifaces

from .protocol import Protocol
from .binary import byte2ports,mac_to_str,mac_to_bytes

logger = logging.getLogger(__name__)

class ConnectionProblem(Exception):
    pass

class Network:

    BROADCAST_ADDR = "255.255.255.255"
    UDP_SEND_TO_PORT = 29808
    UDP_RECEIVE_FROM_PORT = 29809

    def __init__(self, ip_address, host_mac, switch_mac="00:00:00:00:00:00"):
        self.switch_mac = switch_mac
        self.host_mac = host_mac
        self.ip_address = ip_address

        self.sequence_id = random.randint(0, 1000)

        self.header = Protocol.header["blank"].copy()
        self.header.update({
          'sequence_id': self.sequence_id,
          'host_mac':   mac_to_bytes(self.host_mac),
          'switch_mac': mac_to_bytes(self.switch_mac),
        })

        # find interface matching the specified ip_address
        interface = None
        for i in netifaces.interfaces():
             if i != 'lo':
                 addr = netifaces.ifaddresses(i)
                 if netifaces.AF_INET in addr:
                     interface = [i for x in addr[netifaces.AF_INET] if x['addr'] == ip_address][0]

        # Sending socket
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ss.bind((ip_address, Network.UDP_RECEIVE_FROM_PORT))

        # Receiving socket
        self.rs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rs.bind((Network.BROADCAST_ADDR, Network.UDP_RECEIVE_FROM_PORT))
        if interface:
            self.rs.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode())
        self.rs.settimeout(10)

    def send(self, op_code, payload):
        self.sequence_id = (self.sequence_id + 1) % 1000
        self.header.update({
          'sequence_id': self.sequence_id,
          'op_code': op_code,
        })
        packet = Protocol.assemble_packet(self.header, payload)
        logger.debug('Sending Packet: ' + packet.hex())
        packet = Protocol.encode(packet)
        logger.debug('Sending Header:  ' + str(self.header))
        logger.debug('Sending Payload: ' + str(payload))
        self.ss.sendto(packet, (Network.BROADCAST_ADDR, Network.UDP_SEND_TO_PORT))

    def receive(self):
        try:
            data, addr = self.rs.recvfrom(1500)
            data = Protocol.decode(data)
            logger.debug('Receive Packet: ' + data.hex())
            header, payload = Protocol.split(data)
            header, payload = Protocol.interpret_header(header), Protocol.interpret_payload(payload)
            logger.debug('Received Header:  ' + str(header))
            logger.debug('Received Payload: ' + str(payload))
            self.header['token_id'] = header['token_id']
            return header, payload
        except:
            raise ConnectionProblem()

    def query(self, op_code, payload):
        self.send(op_code, payload)
        header, payload = self.receive()
        return header, payload

    def login_dict(self, username, password):
        return [
            (Protocol.get_id('username'), username.encode('ascii') + b'\x00'),
            (Protocol.get_id('password'), password.encode('ascii') + b'\x00'),
        ]

    def login(self, username, password):
        self.query(Protocol.GET, [(Protocol.get_id("get_token_id"), b'')])
        self.query(
            Protocol.LOGIN,
            self.login_dict(username, password)
        )

    def set(self, username, password, payload):
        self.query(Protocol.GET, [(Protocol.get_id("get_token_id"), b'')])
        real_payload = self.login_dict(username, password)
        real_payload += payload
        header, payload = self.query(
            Protocol.LOGIN,
            real_payload
        )
        return header, payload
