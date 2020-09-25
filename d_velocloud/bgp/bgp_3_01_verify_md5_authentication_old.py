from my_velocloud.BaseEdge import BaseEdge
from velocloud import ConfigurationUpdateConfigurationModule, ConfigurationModule
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import json
import time
from ipaddress import ip_address

# Velocloud BGP Settings
# Method populate_bgp_settings() will query Velo Edge and populate them in this global variable
# Only variable to change, if need to, is the 'Segment Name'
VELO_BGP_SETTINGS = {'Segment Name': 'Global Segment',  # Change Segment Name if need to
                     'Segment ID': None,  # Will get populated in populate_bgp_settings()
                     'BGP Enabled': None,  # Will get populated in populate_bgp_settings()
                     'Neighbor': None,  # Will get populated in populate_bgp_settings()
                     'MD5 Password': 'maule123'  # Change if need to
                     }

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'bgp_3_01_verify_md5_authentication.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.224.70'

# VPorts
PORTS = [{'Name': 'Single 840 LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 3,
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

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int, live_mode: bool):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True,
                         live_mode=live_mode)

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

    def populate_bgp_settings(self, segment_name='Global Segment'):
        """
        Populates global variable BGP_SETTINGS by looking at passed Segment (default: Global Segment)

        Gets the following settings:
            is BGP enabled
            Local ASN
            Neighbors list (Only 1 should exists for this test)
        :return: None
        """

        global VELO_BGP_SETTINGS

        # Get all of the Edge's device module data
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get the correct Segment based on parameter segment_name
        segment = self.get_segment_from_module(segment_name=segment_name, module=device_module)

        # if bgp_segment returns as an empty dict, No such segment
        if not segment:
            # No segment named found
            return

        # Segment is found
        # Get BGP Settings from segment
        # Segment name
        VELO_BGP_SETTINGS['Segment Name'] = segment['segment']['name']
        # Segment Id
        VELO_BGP_SETTINGS['Segment ID'] = segment['segment']['segmentId']
        # BGP Enabled
        VELO_BGP_SETTINGS['BGP Enabled'] = segment['bgp']['enabled']
        # Local ASN
        VELO_BGP_SETTINGS['Local ASN'] = segment['bgp']['ASN']
        # Neighbors
        # For this test, there should only be one neighbor
        if not len(segment['bgp']['neighbors']) == 1:
            print('To run this test, there should be 1 neighbor within BGP Settings. '
                  'Please adjust your VeloCloud BGP Settings')
            exit(-1)
        else:
            VELO_BGP_SETTINGS['Neighbor'] = segment['bgp']['neighbors'][0]

    def enable_bgp_md5_auth(self, password):
        """
        Enable MD5 Authentication on Edge BGP Settings Neighbor #1
        On segment: VELO_BGP_SETTINGS['Segment Name']
        :param password: <str> Password for BGP MD5 Auth
        :return: None
        """

        # Get Device Module
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get VELO_BGP_SETTINGS's segment data
        segment = self.get_segment_from_module(segment_name=VELO_BGP_SETTINGS['Segment Name'],
                                               module=device_module)

        # For this test, we are assuming there is only one neighbor in BGP Settings
        # Method populate_bgp_settings() already does this check but we're going to do it again
        if not len(segment['bgp']['neighbors']) == 1:
            print('To run this test, there should be 1 neighbor within BGP Settings. '
                  'Please adjust your VeloCloud BGP Settings')
            exit(-1)

        # Check if MD5 is already enabled if so return
        # Again, since we already check there is only one neighbor in neighbors, we can hard code index 0
        if segment['bgp']['neighbors'][0]['enableMd5']:
            print({'error': None, 'rows': 0})
            return
        else:
            # Enable MD5 and set the password
            segment['bgp']['neighbors'][0]['enableMd5'] = True
            segment['bgp']['neighbors'][0]['md5Password'] = password

        # Setup API parameter
        param = ConfigurationUpdateConfigurationModule(id=device_module.id,
                                                       enterpriseId=self.enterprise_id,
                                                       update=ConfigurationModule(data=device_module.data))
        # Execute API call
        res = EDGE.api.configurationUpdateConfigurationModule(param)

        # Print API response
        print(res)

    def disable_bgp_md5_auth(self):
        """
        Disable MD5 Authentication on Edge BGP Settings Neighbor #1
        On segment: VELO_BGP_SETTINGS['Segment Name']
        :return: None
        """

        # Get Device Module
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get VELO_BGP_SETTINGS's segment data
        segment = self.get_segment_from_module(segment_name=VELO_BGP_SETTINGS['Segment Name'],
                                               module=device_module)

        # For this test, we are assuming there is only one neighbor in BGP Settings
        # Method populate_bgp_settings() already does this check but we're going to do it again
        if not len(segment['bgp']['neighbors']) == 1:
            print('To run this test, there should be 1 neighbor within BGP Settings. '
                  'Please adjust your VeloCloud BGP Settings')
            exit(-1)

        # Check if MD5 is already disabled if so return
        # Again, since we already check there is only one neighbor in neighbors, we can hard code index 0
        if not segment['bgp']['neighbors'][0]['enableMd5']:
            print({'error': None, 'rows': 0})
            return
        else:
            # Disable MD5 and del password
            segment['bgp']['neighbors'][0]['enableMd5'] = False
            try:
                del segment['bgp']['neighbors'][0]['md5Password']
            except KeyError:
                pass

        # Setup API parameter
        param = ConfigurationUpdateConfigurationModule(id=device_module.id,
                                                       enterpriseId=self.enterprise_id,
                                                       update=ConfigurationModule(data=device_module.data))
        # Execute API call
        res = EDGE.api.configurationUpdateConfigurationModule(param)

        # Print API response
        print(res)


# Object for Velocloud
EDGE: BGPRoutingEdge

# Objects for Ixia IxNetwork
SESSION_ASSISTANT: SessionAssistant
IX_NETWORK: SessionAssistant.Ixnetwork
PORT_MAP: SessionAssistant.PortMapAssistant


# noinspection PyTypeChecker
def start_ix_network(enable_md5=False, md5_password=None):
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
    if not ipv4.Ip == VELO_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork IPv4 IP to {VELO_BGP_SETTINGS['Neighbor']['neighborIp']}")
        ipv4.Ip = VELO_BGP_SETTINGS['Neighbor']['neighborIp']

    # Set DUT Port Gateway IP
    # The Gateway IP should be 1 address lower than the Neighbor Ip
    gateway_ip = ip_address(address=VELO_BGP_SETTINGS['Neighbor']['neighborIp']) - 1
    if not ipv4.Gateway == str(gateway_ip):
        IX_NETWORK.info(f"Setting IxNetwork IPv4 Gateway to {gateway_ip}")
        ipv4.Gateway = str(gateway_ip)

    # Set up IPv4 Peers Neighbors
    # First get BGP
    bgp = dut_port.Protocols.find().Bgp
    # Get BGPs Neighbor object
    neighbor = bgp.NeighborRange.find()

    # Set DUT Neighbor BGP ID
    if not neighbor.BgpId == VELO_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork Neighbor BGP ID to {VELO_BGP_SETTINGS['Neighbor']['neighborIp']}")
        neighbor.BgpId = VELO_BGP_SETTINGS['Neighbor']['neighborIp']

    # Set DUT Neighbor BGP DUT IP Address
    # gateway_ip holds the address 1 address lower than the Neighbor IP
    if not neighbor.DutIpAddress == str(gateway_ip):
        IX_NETWORK.info(f"Setting IxNetwork Neighbor DUT IP to {str(gateway_ip)}")
        neighbor.DutIpAddress = str(gateway_ip)

    # Set DUT Neighbor BGP Local AS Number
    if not neighbor.LocalAsNumber == VELO_BGP_SETTINGS['Neighbor']['neighborAS']:
        IX_NETWORK.info(f"Setting IxNetwork Local AS Number to {VELO_BGP_SETTINGS['Neighbor']['neighborAS']}")
        neighbor.LocalAsNumber = VELO_BGP_SETTINGS['Neighbor']['neighborAS']

    # Set DUT Neighbor Local IP Address
    if not neighbor.LocalIpAddress == VELO_BGP_SETTINGS['Neighbor']['neighborIp']:
        IX_NETWORK.info(f"Setting IxNetwork Local IP Address to {VELO_BGP_SETTINGS['Neighbor']['neighborIp']}")
        neighbor.LocalIpAddress = VELO_BGP_SETTINGS['Neighbor']['neighborIp']

    # Enable BGP MD5 Auth on NeighborRange
    if enable_md5:
        if not neighbor.Authentication == 'md5':
            IX_NETWORK.info('Setting BGP NeighborRange Authentication to \'md5\'.')
            neighbor.Authentication = 'md5'

        if not neighbor.Md5Key == md5_password:
            IX_NETWORK.info(f"Setting BGP NeighborRange MD5 password to \'{md5_password}\'")
            neighbor.Md5Key = md5_password
    else:
        if not neighbor.Authentication == 'null':
            IX_NETWORK.info('Setting BGP NeighborRange Authentication to null')
            neighbor.Authentication = 'null'

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
                                                          Timeout=180):
                IX_NETWORK.info('Waiting for BGP Session Up to equal 1...')
                time.sleep(10)
        except SyntaxError:
            continue
        except NotFoundError:
            print({'error': "BGP Session Timeout"})
            return
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
    # EDGE.LiveMode.exit_live_mode()


def check_bgp_settings():
    EDGE.check_bgp_settings()


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
    while True:
        try:
            # noinspection PyTypeChecker
            print(EDGE.LiveMode.get_bgp_neighbor_received_routes(
                segment_id=VELO_BGP_SETTINGS['Segment ID'],
                neighbor_ip=VELO_BGP_SETTINGS['Neighbor']['neighborIp']))
        except TimeoutError:
            print('get_bgp_neighbor_received_routes timed out. Trying again...')
            time.sleep(10)
            continue
        break


def get_bgp_neighbor_advertised_routes(ip='192'):
    while True:
        try:
            # noinspection PyTypeChecker
            print(EDGE.LiveMode.get_bgp_neighbor_advertised_routes(
                segment_id=VELO_BGP_SETTINGS['Segment ID'],
                neighbor_ip=VELO_BGP_SETTINGS['Neighbor']['neighborIp']))
        except TimeoutError:
            print('get_bgp_neighbor_advertised_routes timed out. Trying again...')
            time.sleep(10)
            continue
        break


def get_bgp_summary():
    while True:
        try:
            print(EDGE.LiveMode.get_bgp_summary())
        except TimeoutError:
            print('get_bgp_summary timed out. Trying again...')
            time.sleep(10)
            continue
        break


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0, live_mode=True)
    EDGE.populate_bgp_settings(segment_name=VELO_BGP_SETTINGS['Segment Name'])


def enable_bgp_md5_auth(password=VELO_BGP_SETTINGS['MD5 Password']):
    EDGE.enable_bgp_md5_auth(password=password)


def disable_bgp_md5_auth():
    EDGE.disable_bgp_md5_auth()


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    # EDGE.enable_bgp_md5_auth(password=VELO_BGP_SETTINGS['MD5 Password'])
    EDGE.disable_bgp_md5_auth()
