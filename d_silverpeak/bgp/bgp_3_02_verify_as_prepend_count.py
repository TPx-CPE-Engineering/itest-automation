from my_silverpeak.base_edge import SPBaseEdge
from my_silverpeak.Globals import DEFAULT_BGP_INFORMATION
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'bgp_3_02_verify_as_prepend_count_SP.ixncfg'
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

    def set_as_prepend_count_on_bgp_peer(self, as_prepend_count, bgp_peer_ip):
        """
        Enables AS Prepend Count for a BGP Peer
        :param as_prepend_count: <int> 0-10
        :param bgp_peer_ip: <str> IP of BGP Peer
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data
        try:
            if bgp_config_neighbors[bgp_peer_ip]['as_prepend'] == as_prepend_count:
                print({'error': None, 'rows': 0})
                return
        except KeyError:
            print(f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.')

        # else
        bgp_config_neighbors[bgp_peer_ip]['as_prepend'] = as_prepend_count

        response = EDGE.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print(response.error)
            exit(-1)
        print({'error': None, 'rows': 1, 'data': response.data})

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

    # SESSION_ASSISTANT = SessionAssistant(IpAddress=IX_NET_CHASSIS_IP,
    #                                      LogLevel=SessionAssistant.LOGLEVEL_INFO,
    #                                      ClearConfig=False)
    #
    # # Get IxNetwork object from Session
    # IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

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


def set_as_prepend_count(count=5):
    # Grab default Peer IP, default Peer is the first in the list, Silverpeak uses its IP as key for dict.
    default_peer = DEFAULT_BGP_INFORMATION['BGP Peers'][0]
    default_peer_ip = next(iter(default_peer))

    EDGE.set_as_prepend_count_on_bgp_peer(as_prepend_count=count, bgp_peer_ip=default_peer_ip)


def do_ix_network_routes_match_as_prepend_count(count=5):

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
    time.sleep(10)

    ipv4_unicast = dut_port.Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    match_as_prepend_count = True
    for ip in ipv4_unicast:
        as_path = ip.AsPath.strip("<>").split(" ")
        if not len(as_path) == count + 1:
            match_as_prepend_count = False
            break

    if match_as_prepend_count:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    routes = []
    for ip in ipv4_unicast:
        routes.append({'IP': ip.IpPrefix + '/' + str(ip.PrefixLength), 'AsPath': ip.AsPath})
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