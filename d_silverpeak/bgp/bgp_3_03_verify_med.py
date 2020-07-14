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

# BGP_SETTINGS = {
#     'enable': True,
#     'asn': 64515,
#     'rtr_id': '192.168.131.1',
#     'graceful_restart_en': False,
#     'max_restart_time': 120,
#     'stale_path_time': 150,
#     'remote_as_path_advertise': False,
#     'redist_ospf': True,
#     'redist_ospf_filter': 0,
#     'log_nbr_msgs': True,
#     'BGP Peer': {
#         '192.168.131.99': {
#             'enable': True,
#             'self': '192.168.131.99',
#             'remote_as': 64514,
#             'import_rtes': True,
#             'type': 'Branch',
#             'loc_pref': 100,
#             'med': 60,
#             'as_prepend': 5,
#             'next_hop_self': False,
#             'in_med': 0,
#             'ka': 30,
#             'hold': 90,
#             'export_map': 4294967295,
#             'password': ''
#         }
#     }
# }

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'bgp_3_03_verify_med_SP.ixncfg'
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

    def set_med_on_bgp_peer(self, med, bgp_peer_ip):
        """
        Sets MED for a BGP Peer
        :param med: <int> MED for Peer
        :param bgp_peer_ip: <str> IP of BGP Peer
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        try:
            if bgp_config_neighbors[bgp_peer_ip]['med'] == med:
                print({'error': None, 'rows': 0, 'data': f"MED already set to {med}."})
                return
        except KeyError:
            print(f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.')
            exit(-1)

        # else
        bgp_config_neighbors[bgp_peer_ip]['med'] = med

        response = EDGE.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print({'error': None, 'rows': 1, 'data': response.data})

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

        # For this test we want external BGP so make sure the ASN from Silverpeak and BGP Peer are different
        if SP_BGP_SETTINGS['ASN'] == SP_BGP_SETTINGS['BGP Peer']['Remote ASN']:
            print('To run this test, we need Edge ASN and BGP Peer ASN to be different to create an external BGP')
            exit(-1)

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

    # First get BGP
    bgp = dut_port.Protocols.find().Bgp

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


def get_bgp_summary():
    while True:
        try:
            EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def set_med(med=55):
    EDGE.set_med_on_bgp_peer(med=med, bgp_peer_ip=SP_BGP_SETTINGS['BGP Peer']['IP'])


def do_ix_network_routes_match_med(med=55):

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

    # Refresh routes
    neighbor_range = dut_port.Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()
    time.sleep(5)

    ipv4_unicast = dut_port.Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    med_match = True
    # search through every ip and check if its med matches
    for ip in ipv4_unicast:
        if not ip.MultiExitDiscriminator == med:
            med_match = False
            break

    if med_match:
        # All ips matched med
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    # Print every IP with its MED
    routes = []
    for ip in ipv4_unicast:
        routes.append({'IP': ip.IpPrefix + '/' + str(ip.PrefixLength), 'MED': ip.MultiExitDiscriminator})

    print(routes)


def create_edge(edge_id, enterprise_id=None):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    temp_bgp_information = copy.deepcopy(DEFAULT_BGP_INFORMATION)
    # Test requirements:
    #   eBGP
    #
    # By default BGP is set to iBGP
    # For eBGP, Edge ASN must be different than the Peer ASN

    # Grab default Peer IP, default Peer is the first in the list, Silverpeak uses its IP as key for dict.
    default_peer = temp_bgp_information['BGP Peers'][0]
    default_peer_ip = next(iter(default_peer))

    # Set Config System ASN to BGP Peer ASN + 1 in order to be different and have eBGP
    temp_bgp_information['Config System']['asn'] = default_peer[default_peer_ip]['remote_as'] + 1

    EDGE.set_bgp_settings(bgp_settings=temp_bgp_information)
    time.sleep(5)

    EDGE.disable_bgp()
    time.sleep(10)
    EDGE.enable_bgp()
    time.sleep(30)


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
