from my_silverpeak.base_edge import SPBaseEdge
from my_silverpeak.Globals import DEFAULT_BGP_INFORMATION
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time
import copy
from ipaddress import ip_address

# SilverPeak BGP Settings
# Method populate_bgp_settings() will query SP Edge and populate them in this global variable

SP_BGP_SETTINGS = {
                   'ASN': '64514',
                   'Router ID': '192.168.131.1',
                   'BGP Peer': {
                       'IP': '192.168.131.99',
                       'Remote ASN': 64514,
                       'Type': 'Branch',
                       'Admin Status': 'UP',
                       'Local Preference': 100
                        }
                   }
# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'bgp_3_00_verify_neighbor_adjacency_advertised_received_routes_SP.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.224.70'

# VPorts
PORTS = [{'Name': 'LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 1,
          'DUT': True
          }]

# Force ownership of ports
FORCE_OWNERSHIP = True


class BGPRoutingEdge(SPBaseEdge):

    def __init__(self, edge_id: str, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)

    def enable_bgp(self):
        """
        Enables BGP on Edge
        :return: None
        """
        # Get existing BGP config system data
        bgp_config_sys = self.api.get_bgp_config_system(applianceID=self.edge_id).data

        # Set BGP to disable
        bgp_config_sys['enable'] = True

        # Post change
        response = EDGE.api.post_bgp_config_system(applianceID=self.edge_id, bgpConfigSystemData=json.dumps(bgp_config_sys))
        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print('Edge BGP Enabled successfully')

    def disable_bgp(self):
        """
        Disables BGP on Edge
        :return: None
        """
        # Get existing BGP config system data
        bgp_config_sys = self.api.get_bgp_config_system(applianceID=self.edge_id).data

        # Set BGP to disable
        bgp_config_sys['enable'] = False

        # Post change
        response = EDGE.api.post_bgp_config_system(applianceID=self.edge_id, bgpConfigSystemData=json.dumps(bgp_config_sys))
        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print('Edge BGP Disabled successfully')

    def populate_bgp_settings(self):
        global SP_BGP_SETTINGS

        # Get BGP Config System Settings to obtain BGP Router ID and ASN
        bgp_config_system = self.api.get_bgp_config_system(applianceID=self.edge_id).data

        # Set BGP Router ID
        SP_BGP_SETTINGS['Router ID'] = bgp_config_system['rtr_id']

        # Set BGP ASN
        SP_BGP_SETTINGS['ASN'] = bgp_config_system['asn']

        # Now get BGP Neighbors (Peers)
        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        # Make sure theres only 1 neighbor
        if not len(bgp_config_neighbors) == 1:
            print('To run this test, there should be 1 neighbor within BGP Settings. '
                  'Please adjust your SilverPeak BGP Settings')
            exit(-1)

        # Because SP uses the neighbor ip as a key, we must get it (assuming there is only one neighbor)
        neighbor_key = list(bgp_config_neighbors.keys())[0]

        # Set BGP Peer - IP
        SP_BGP_SETTINGS['BGP Peer']['IP'] = bgp_config_neighbors[neighbor_key]['self']

        # Set BGP Peer - Remote ASN
        SP_BGP_SETTINGS['BGP Peer']['Remote ASN'] = bgp_config_neighbors[neighbor_key]['remote_as']

        # Set BGP Peer - Type
        SP_BGP_SETTINGS['BGP Peer']['Type'] = bgp_config_neighbors[neighbor_key]['type']

        # Set BGP Peer - Admin Status Enable
        SP_BGP_SETTINGS['BGP Peer']['Admin Status Enable'] = bgp_config_neighbors[neighbor_key]['enable']

        # Set BGP Peer - Local Preference
        SP_BGP_SETTINGS['BGP Peer']['Local Preference'] = bgp_config_neighbors[neighbor_key]['loc_pref']

    def get_bgp_summary(self):
        """
        Gets Edge BGP Summary
        :return: None
        """

        bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)

        neighbors_state = []
        for neighbor in bgp_state.data['neighbor']['neighborState']:
            neighbors_state.append({'neighbor': neighbor['peer_ip'],
                                    'state': neighbor['peer_state_str']})

        print(neighbors_state)

    def get_bgp_route_table(self):
        bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)

        # print(json.dumps(bgp_state.data))
        print(bgp_state.data['rttable'])

    def set_bgp_settings(self, bgp_settings):
        """
        Sets Edge's BGP Settings
        :param bgp_settings: bgp settings config, must match global DEFAULT_BGP_INFORMATION structure
        :return:
        """

        # Push BGP Config System
        response = EDGE.api.post_bgp_config_system(applianceID=self.edge_id,
                                                   bgpConfigSystemData=json.dumps(bgp_settings['Config System']))
        # Check response status
        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print({'error': None, 'rows': 1, 'data': response.data})

        # Set the BGP Peers Config
        # First Peer is the default Peer
        neighbors_config = bgp_settings['BGP Peers'][0]

        # Push BGP Peers config
        response = EDGE.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(neighbors_config))
        # Check response status
        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print({'error': None, 'rows': 1, 'data': response.data})


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
    IX_NETWORK.info(f'Loading config: {IX_NET_CONFIG_FILE}...')
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

    # # Set DUT Port Local IP
    # ipv4 = dut_port.Interface.find().Ipv4.find()
    # if not ipv4.Ip == SP_BGP_SETTINGS['BGP Peer']['IP']:
    #     IX_NETWORK.info(f"Setting IxNetwork IPv4 IP to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
    #     ipv4.Ip = SP_BGP_SETTINGS['BGP Peer']['IP']
    #
    # # Set DUT Port Gateway IP
    # if not ipv4.Gateway == SP_BGP_SETTINGS['Router ID']:
    #     IX_NETWORK.info(f"Setting IxNetwork IPv4 Gateway to {SP_BGP_SETTINGS['Router ID']}")
    #     ipv4.Gateway = SP_BGP_SETTINGS['Router ID']

    # Set up IPv4 Peers Neighbors
    # First get BGP
    bgp = dut_port.Protocols.find().Bgp
    # Get BGPs Neighbor object
    neighbor = bgp.NeighborRange.find()

    # # Set DUT Neighbor BGP ID
    # if not neighbor.BgpId == SP_BGP_SETTINGS['BGP Peer']['IP']:
    #     IX_NETWORK.info(f"Setting IxNetwork Neighbor BGP ID to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
    #     neighbor.BgpId = SP_BGP_SETTINGS['BGP Peer']['IP']
    #
    # # Set DUT Neighbor BGP DUT IP Address
    # if not neighbor.DutIpAddress == SP_BGP_SETTINGS['Router ID']:
    #     IX_NETWORK.info(f"Setting IxNetwork Neighbor DUT IP to {SP_BGP_SETTINGS['Router ID']}")
    #     neighbor.DutIpAddress = SP_BGP_SETTINGS['Router ID']
    #
    # # Set DUT Neighbor BGP Local AS Number
    # if not neighbor.LocalAsNumber == SP_BGP_SETTINGS['ASN']:
    #     IX_NETWORK.info(f"Setting IxNetwork Local AS Number to {SP_BGP_SETTINGS['ASN']}")
    #     neighbor.LocalAsNumber = SP_BGP_SETTINGS['ASN']
    #
    # # Set DUT Neighbor Local IP Address
    # if not neighbor.LocalIpAddress == SP_BGP_SETTINGS['BGP Peer']['IP']:
    #     IX_NETWORK.info(f"Setting IxNetwork Local IP Address to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
    #     neighbor.LocalIpAddress = SP_BGP_SETTINGS['BGP Peer']['IP']

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
                                                          ConditionValue=1,
                                                          Timeout=120):
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

    # Reset BGP settings to default on Edge
    EDGE.set_bgp_settings(bgp_settings=DEFAULT_BGP_INFORMATION)


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

    # Refresh the routes
    neighbor_range = dut_port.Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()
    time.sleep(10)
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
    while True:
        try:
            EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def create_edge(edge_id, enterprise_id=None):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    temp_bgp_information = copy.deepcopy(DEFAULT_BGP_INFORMATION)
    # Test requirements:
    #   iBGP
    #
    # By default BGP is set to iBGP

    EDGE.set_bgp_settings(bgp_settings=temp_bgp_information)
    time.sleep(5)

    EDGE.disable_bgp()
    time.sleep(10)
    EDGE.enable_bgp()
    time.sleep(30)


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
    get_bgp_neighbor_advertised_routes()

