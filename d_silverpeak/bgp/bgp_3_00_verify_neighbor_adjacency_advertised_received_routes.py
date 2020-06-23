from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time
from ipaddress import ip_address

# SilverPeak BGP Settings
# Method populate_bgp_settings() will query SP Edge and populate them in this global variable

SP_BGP_SETTINGS = {'Segment Name': 'Global Segment',  # Change Segment Name if need to
                   'Segment ID': None,  # Will get populated in populate_bgp_settings()
                   'BGP Enabled': None,  # Will get populated in populate_bgp_settings()
                   'Neighbor': None,  # Will get populated in populate_bgp_settings()

                   'ASN': '64514',
                   'Router ID': '192.168.131.1',
                   'BGP Peers': [{
                       'IP': '192.168.131.99',
                       'Remote ASN': 64514,
                       'Type': 'Branch',
                       'Admin Status': 'UP',
                       'Local Preference': 100
                   }]
                   }
# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'bgp_3_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.224.70'

# VPorts
PORTS = [{'Name': 'Single 540 LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 1,
          'DUT': True
          },
         {'Name': '520HA LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 3,
          'DUT': False
          }]

# Force ownership of ports
FORCE_OWNERSHIP = True


class BGPRoutingEdge(SPBaseEdge):

    def __init__(self, edge_id: str, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)

    def populate_bgp_settings(self):
        global SP_BGP_SETTINGS
        print(self.edge_id)

    def get_bgp_summary(self):

        bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)

        neighbors_state = []
        for neighbor in bgp_state.data['neighbor']['neighborState']:
            neighbors_state.append({'neighbor': neighbor['peer_ip'],
                                    'state': neighbor['peer_state_str']})

        # TODO check in iTest is response below works
        print(neighbors_state)
        return neighbors_state

    def get_bgp_route_table(self):
        bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)

        # print(json.dumps(bgp_state.data))
        print(bgp_state.data['rttable'])


# Object for SilverPeak
EDGE: BGPRoutingEdge

# Objects for Ixia IxNetwork
SESSION_ASSISTANT: SessionAssistant
IX_NETWORK: SessionAssistant.Ixnetwork
PORT_MAP: SessionAssistant.PortMapAssistant


# noinspection PyTypeChecker
def start_ix_network():
    # Initiate IxNetwork session
    global PORT_MAP, SESSION_ASSISTANT, IX_NETWORK

    # Initiate Session
    SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=True)

    # Get IxNetwork object from Session
    IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Load Config
    IX_NETWORK.info('Loading config...')
    try:
        IX_NETWORK.LoadConfig(Files(file_path=FULL_CONFIG, local_file=True))
    except BadRequestError as e:
        print({'error': f"{e.message}"})
        exit(-1)
    IX_NETWORK.info('Config loaded.')

    PORT_MAP = SESSION_ASSISTANT.PortMapAssistant()

    # Connect every port in PORTS
    for port in PORTS:
        PORT_MAP.Map(IpAddress=port['Chassis IP'],
                     CardId=port['Card'],
                     PortId=port['Port'],
                     Name=port['Name'])

    IX_NETWORK.info('Connecting to ports...')
    PORT_MAP.Connect(ForceOwnership=FORCE_OWNERSHIP)
    IX_NETWORK.info('Ports connected.')

    # Set DUT Port based on DUT property in global PORTS
    dut_port = None
    for port in PORTS:
        if port['DUT']:
            dut_port = IX_NETWORK.Vport.find(Name=port['Name'])
            break

    # Set DUT Port Local IP
    ipv4 = dut_port.Interface.find().Ipv4.find()
    if not ipv4.Ip == SP_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork IPv4 IP to {SP_BGP_SETTINGS['Neighbor']['neighborIp']}")
        ipv4.Ip = SP_BGP_SETTINGS['Neighbor']['neighborIp']

    # Set DUT Port Gateway IP
    # The Gateway IP should be 1 address lower than the Neighbor Ip
    gateway_ip = ip_address(address=SP_BGP_SETTINGS['Neighbor']['neighborIp']) - 1
    if not ipv4.Gateway == str(gateway_ip):
        IX_NETWORK.info(f"Setting IxNetwork IPv4 Gateway to {gateway_ip}")
        ipv4.Gateway = str(gateway_ip)

    # Set up IPv4 Peers Neighbors
    # First get BGP
    bgp = dut_port.Protocols.find().Bgp
    # Get BGPs Neighbor object
    neighbor = bgp.NeighborRange.find()

    # Set DUT Neighbor BGP ID
    if not neighbor.BgpId == SP_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork Neighbor BGP ID to {SP_BGP_SETTINGS['Neighbor']['neighborIp']}")
        neighbor.BgpId = SP_BGP_SETTINGS['Neighbor']['neighborIp']

    # Set DUT Neighbor BGP DUT IP Address
    # gateway_ip holds the address 1 address lower than the Neighbor IP
    if not neighbor.DutIpAddress == str(gateway_ip):
        IX_NETWORK.info(f"Setting IxNetwork Neighbor DUT IP to {str(gateway_ip)}")
        neighbor.DutIpAddress = str(gateway_ip)

    # Set DUT Neighbor BGP Local AS Number
    if not neighbor.LocalAsNumber == SP_BGP_SETTINGS['Neighbor']['neighborAS']:
        IX_NETWORK.info(f"Setting IxNetwork Local AS Number to {SP_BGP_SETTINGS['Neighbor']['neighborAS']}")
        neighbor.LocalAsNumber = SP_BGP_SETTINGS['Neighbor']['neighborAS']

    # Set DUT Neighbor Local IP Address
    if not neighbor.LocalIpAddress == SP_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork Local IP Address to {SP_BGP_SETTINGS['Neighbor']['neighborIp']}")
        neighbor.LocalIpAddress = SP_BGP_SETTINGS['Neighbor']['neighborIp']

    # Start protocols
    # IX_NETWORK.info('Starting protocols...')
    # IX_NETWORK.StartAllProtocols()
    IX_NETWORK.info('Starting BGP Protocol...')
    bgp.Start()
    time.sleep(10)
    IX_NETWORK.info('BGP Protocol started.')

    # Wait until Sess. Up is 1
    IX_NETWORK.info('Checking for BGP Session Up...')
    bgp_aggregated_stats = SESSION_ASSISTANT.StatViewAssistant(ViewName='BGP Aggregated Statistics', Timeout=180)

    while True:
        try:
            while not bgp_aggregated_stats.CheckCondition(ColumnName='Sess. Up',
                                                          Comparator=StatViewAssistant.EQUAL,
                                                          ConditionValue=1):
                IX_NETWORK.info('Waiting for BGP Session Up to equal 1...')
                time.sleep(10)
        except SyntaxError:
            continue
        break

    IX_NETWORK.info('BGP Session Up.')


def stop_ix_network():
    # Stop protocols
    IX_NETWORK.info('Stopping protocols...')
    IX_NETWORK.StopAllProtocols()
    IX_NETWORK.info('Protocols stopped.')

    # Disconnect PORTS
    IX_NETWORK.info('Disconnecting ports...')
    PORT_MAP.Disconnect()
    IX_NETWORK.info('Port disconnected.')


def check_bgp_settings():
    print('todo')


def do_advertise_routes_match(edges_routes):
    """
    Prints yes or no if IxNetwork IPv4 Unicast Routes IP's match with Velo BGP Neighbor Advertised Routes IPs
    :param edges_routes: <list> Velo BGP Neighbor Advertised Routes IPs
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_advertise_routes_ips = []
    for route in edges_routes:
        edge_advertise_routes_ips.append(route.split('/')[0])

    # # Initiate globals for testing.
    # # Comment out for iTest run
    # SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
    #                                      LogLevel=SessionAssistant.LOGLEVEL_INFO,
    #                                      ClearConfig=False)
    #
    # # Get IxNetwork object from Session
    # IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Get DUT Port based on PORTS DUT property
    dut_port = None
    for port in PORTS:
        if port['DUT']:
            dut_port = IX_NETWORK.Vport.find(Name=port['Name'])
            break

    ipv4_unicast = dut_port.Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    # Create list of ips taken from Protocol -> BGP
    # -> DUT Port -> IPv4 Peers -> 'Internal - 192.168.144.2-1' -> Learned Routes
    ix_network_advertise_routes_ips = []
    for ip in ipv4_unicast:
        ix_network_advertise_routes_ips.append(ip.IpPrefix)

    # Check if the ips match, expecting to match to pass the test
    if edge_advertise_routes_ips == ix_network_advertise_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Advertise Routes IPs': edge_advertise_routes_ips})
    print({'IxNetwork Advertise Routes IPs': ix_network_advertise_routes_ips})


def do_received_routes_match(edges_routes):
    """
    Prints yes or no if IxNetwork Route Range IPs match with Velo BGP Recieved Routes IPs
    :param edges_routes: <list> Velo BGP Neighbor Received Routes
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_received_routes_ips = []
    for route in edges_routes:
        edge_received_routes_ips.append(route.split('/')[0])

    # # Initiate globals for testing.
    # # Comment out for iTest run
    # SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
    #                                      LogLevel=SessionAssistant.LOGLEVEL_INFO,
    #                                      ClearConfig=False)
    #
    # # Get IxNetwork object from Session
    # IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Get DUT Port based on PORTS DUT property
    dut_port = None
    for port in PORTS:
        if port['DUT']:
            dut_port = IX_NETWORK.Vport.find(Name=port['Name'])
            break

    route_ranges = dut_port.Protocols.find().Bgp.NeighborRange.find().RouteRange.find()

    # Gather Ix Network Routes IPs
    ix_network_received_routes_ips = []
    for route in route_ranges:
        number_of_routes = route.NumRoutes
        ip = ip_address(address=route.NetworkAddress)
        while number_of_routes > 0:
            ix_network_received_routes_ips.append(str(ip))
            # Increase IP by 256
            ip = ip + 256
            number_of_routes -= 1

    if edge_received_routes_ips == ix_network_received_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Received Routes IPs': edge_received_routes_ips})
    print({'IxNetwork Received Routes IPs': ix_network_received_routes_ips})


def get_bgp_neighbor_received_routes():
    EDGE.get_bgp_route_table()


def get_bgp_neighbor_advertised_routes():
    EDGE.get_bgp_route_table()


def get_bgp_summary():
    EDGE.get_bgp_summary()


def create_edge(edge_id, enterprise_id=None):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)
    EDGE.populate_bgp_settings()


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
    get_bgp_neighbor_advertised_routes()

