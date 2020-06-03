from my_velocloud.BaseEdge import BaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time
from ipaddress import ip_address

# Velocloud BGP Settings
# Method populate_bgp_settings() will query Velo Edge and populate them in this global variable
# Only variable to change, if need to, is the Segment Name.
VELO_BGP_SETTINGS = {'Segment Name': 'Global Segment',  # Change Segment Name if need to
                     'Segment ID': None,
                     'BGP Enabled': None,
                     'Neighbor': None
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


class BGPRoutingEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True,
                         live_mode=True)

    def check_bgp_settings(self):
        """
        Check if Edge's BGP Settings match BGP_SETTINGS
        :return: None
        """

        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')
        # print(json.dumps(device_module))

        # Check #1 BGP_SETTINGS['Segment Name']
        bgp_settings_segment = self.get_segment_from_module(segment_name=VELO_BGP_SETTINGS['Segment Name'],
                                                            module=device_module)
        if not bgp_settings_segment:
            print({'error': f"No Configure Segment: {VELO_BGP_SETTINGS['Segment Name']} found."})
            exit(-1)

        # Within BGP_SETTINGS['Segment Name'] check for the rest of BGP Settings
        # Check #2 BGP_SETTINGS['BGP Enabled']
        if not bgp_settings_segment['bgp']['enabled']:
            print({'error': f"BGP Enabled is: {bgp_settings_segment['bgp']['enabled']}. "
                            f"Expecting: {VELO_BGP_SETTINGS['BGP Enabled']}."})
            exit(-1)

        # Check #3 BGP_SETTINGS['Local ASN']
        if not bgp_settings_segment['bgp']['ASN'] == VELO_BGP_SETTINGS['Local ASN']:
            print({'error': f"Local ASN is: {bgp_settings_segment['bgp']['ASN']}. "
                            f"Expecting: {VELO_BGP_SETTINGS['Local ASN']}."})
            exit(-1)

        # Check #4 BGP_SETTINGS['Neighbor IP']
        # Check #5 BGP_SETTINGS['Neighbor ASN']
        check_pass = False
        for neighbor in bgp_settings_segment['bgp']['neighbors']:
            if neighbor['neighborIp'] == VELO_BGP_SETTINGS['Neighbor IP'] and \
                    neighbor['neighborAS'] == VELO_BGP_SETTINGS['Neighbor ASN']:
                check_pass = True
                break

        if not check_pass:
            print({'error': f"No Neighbor IP: {VELO_BGP_SETTINGS['Neighbor IP']} with ASN: "
                            f"{VELO_BGP_SETTINGS['Neighbor ASN']} found."})
            exit(-1)

        print({'error': None})


# Object for Velocloud
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

    time.sleep(35)

    # Start protocols
    # IX_NETWORK.info('Starting protocols...')
    # IX_NETWORK.StartAllProtocols()
    IX_NETWORK.info('Starting BGP Protocol...')
    v_port = IX_NETWORK.Vport.find(Name='Single 540 LAN')
    bgp = v_port.Protocols.find().Bgp
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

    # Exit out of EDGE Live Mode gracefully
    EDGE.LiveMode.exit_live_mode()


def check_bgp_settings():
    EDGE.check_bgp_settings()


def do_advertise_routes_match(edges_routes):
    # Variable 'edges_routes' sometimes with subnet mask ex. 4.2.2.2/32. 'edges_routes' comes from VC BGP Neighbor Advertised Function.
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

    ipv4_unicast = IX_NETWORK.Vport.find(Name='Single 540 LAN').Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    # Create list of ips taken from Protocol -> BGP -> 'Single 540 LAN' -> IPv4 Peers -> 'Internal - 192.168.144.2-1' -> Learned Routes
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
    # Variable 'edges_routes' comes with subnet mask.
    # Remove subnet mask to make verifying matching easier.
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

    route_ranges = IX_NETWORK.Vport.find(Name='Single 540 LAN').Protocols.find().Bgp.NeighborRange.find().RouteRange.find()

    ix_network_received_routes_ips = []
    for route in route_ranges:
        number_of_routes = route.NumRoutes
        ip = ip_address(address=route.NetworkAddress)
        while number_of_routes > 0:
            ix_network_received_routes_ips.append(str(ip))
            ip = ip + 256
            number_of_routes -= 1

    if edge_received_routes_ips == ix_network_received_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Received Routes IPs': edge_received_routes_ips})
    print({'IxNetwork Received Routes IPs': ix_network_received_routes_ips})


def get_bgp_neighbor_received_routes():
    while True:
        try:
            print(EDGE.LiveMode.get_bgp_neighbor_received_routes(segment_id=0, neighbor_ip='192.168.144.2'))
        except TimeoutError:
            print('error time out')
            continue
        break


def get_bgp_neighbor_advertised_routes(ip='192'):
    while True:
        try:
            print(EDGE.LiveMode.get_bgp_neighbor_advertised_routes(segment_id=0, neighbor_ip='192.168.144.2'))
        except TimeoutError:
            print('Time out error. Trying again')
            continue
        break


def get_bgp_summary():
    while True:
        try:
            print(EDGE.LiveMode.get_bgp_summary())
        except TimeoutError:
            print('Time out error. Trying again')
            time.sleep(10)
            continue
        break


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0)


if __name__ == '__main__':
    create_edge(edge_id=3, enterprise_id=1)
    # check_bgp_settings()
    # start_ix_network()
    # do_advertise_routes_match(edges_routes=['4.2.2.2/32', '10.0.1.0/30', '10.0.2.0/30', '10.0.3.0/30', '10.0.80.0/30', '10.0.81.0/30', '10.0.82.0/30',
    #                                               '10.0.83.0/30', '10.0.86.0/30', '10.0.87.0/30', '10.0.88.0/30', '10.10.1.0/30', '10.10.32.0/30',
    #                                               '10.10.84.0/24', '10.33.34.0/30', '66.66.66.66/32', '172.16.33.0/29', '192.168.17.0', '192.168.24.0',
    #                                               '192.168.44.0', '192.168.53.0', '192.168.84.0', '192.168.99.1/32', '192.168.101.0', '192.168.124.0',
    #                                               '192.168.144.0', '192.168.164.0', '192.168.184.0', '192.168.221.0', '208.57.7.36/32'])
    # do_received_routes_match(edges_routes=['4.2.2.2/32'])
    get_bgp_neighbor_received_routes()
