from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time
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
IX_NET_CONFIG_FILE = 'bgp_3_02_verify_as_prepend_count_SP.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.20.7'

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
                print({'error': None, 'rows': 0})
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
    if not ipv4.Ip == SP_BGP_SETTINGS['BGP Peer']['IP']:
        IX_NETWORK.info(f"Setting IxNetwork IPv4 IP to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
        ipv4.Ip = SP_BGP_SETTINGS['BGP Peer']['IP']

    # Set DUT Port Gateway IP
    if not ipv4.Gateway == SP_BGP_SETTINGS['Router ID']:
        IX_NETWORK.info(f"Setting IxNetwork IPv4 Gateway to {SP_BGP_SETTINGS['Router ID']}")
        ipv4.Gateway = SP_BGP_SETTINGS['Router ID']

    # Set up IPv4 Peers Neighbors
    # First get BGP
    bgp = dut_port.Protocols.find().Bgp
    # Get BGPs Neighbor object
    neighbor = bgp.NeighborRange.find()

    # Set DUT Neighbor BGP ID
    if not neighbor.BgpId == SP_BGP_SETTINGS['BGP Peer']['IP']:
        IX_NETWORK.info(f"Setting IxNetwork Neighbor BGP ID to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
        neighbor.BgpId = SP_BGP_SETTINGS['BGP Peer']['IP']

    # Set DUT Neighbor BGP DUT IP Address
    if not neighbor.DutIpAddress == SP_BGP_SETTINGS['Router ID']:
        IX_NETWORK.info(f"Setting IxNetwork Neighbor DUT IP to {SP_BGP_SETTINGS['Router ID']}")
        neighbor.DutIpAddress = SP_BGP_SETTINGS['Router ID']

    # # Set DUT Neighbor BGP Local AS Number
    # if not neighbor.LocalAsNumber == SP_BGP_SETTINGS['ASN']:
    #     IX_NETWORK.info(f"Setting IxNetwork Local AS Number to {SP_BGP_SETTINGS['ASN']}")
    #     neighbor.LocalAsNumber = SP_BGP_SETTINGS['ASN']

    # Set DUT Neighbor Local IP Address
    if not neighbor.LocalIpAddress == SP_BGP_SETTINGS['BGP Peer']['IP']:
        IX_NETWORK.info(f"Setting IxNetwork Local IP Address to {SP_BGP_SETTINGS['BGP Peer']['IP']}")
        neighbor.LocalIpAddress = SP_BGP_SETTINGS['BGP Peer']['IP']

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

    SESSION_ASSISTANT = SessionAssistant(IpAddress=IX_NET_CHASSIS_IP,
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=False)

    # Get IxNetwork object from Session
    IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Stop protocols
    IX_NETWORK.info('Stopping protocols...')
    IX_NETWORK.StopAllProtocols()
    IX_NETWORK.info('Protocols stopped.')

    # # Disconnect PORTS
    # IX_NETWORK.info('Disconnecting ports...')
    # PORT_MAP.Disconnect()
    # IX_NETWORK.info('Port disconnected.')


def get_bgp_summary():
    while True:
        try:
            EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def set_as_prepend_count(count=5):
    EDGE.set_as_prepend_count_on_bgp_peer(as_prepend_count=count, bgp_peer_ip=SP_BGP_SETTINGS['BGP Peer']['IP'])


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
    EDGE.populate_bgp_settings()
    EDGE.disable_bgp()
    time.sleep(10)
    EDGE.enable_bgp()
    time.sleep(30)


if __name__ == '__main__':
    # create_edge(edge_id='18.NE')
    # EDGE.set_as_prepend_count_on_bgp_peer(as_prepend_count=0, bgp_peer_ip='192.168.131.99')
    # EDGE.set_med_on_bgp_peer(med=57, bgp_peer_ip='192.168.131.199')
    # EDGE.get_bgp_summary()
    # start_ix_network()
    do_ix_network_routes_match_as_prepend_count(count=5)