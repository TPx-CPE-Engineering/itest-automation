from my_velocloud.BaseEdge import BaseEdge
from velocloud import ConfigurationUpdateConfigurationModule
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import json
import time
from ipaddress import ip_address

# Velocloud BGP Settings
# Method populate_bgp_settings() will query Velo Edge and populate them in this global variable
# Only variable to change, if need to, is the 'Segment Name'
VELO_OSPF_SETTINGS = {'Segment Name': 'Global Segment',  # CHANGE Segment Name if need to
                      'Segment ID': None,  # Will get populated in populate_ospf_settings()
                      'VLAN Name': 'Corporate',  # CHANGE VLAN Name if need too
                      'VLAN ID': None,  # Will get populated in populate_ospf_settings()
                      'VLAN IP Address': None,
                      'Interface Name': 'GE2',  # CHANGE Interface if need too
                      'Management IP': None #  Will get populated in populate_ospf_settings()
                      }

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'ospf_2_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.224.70'

# VPorts
PORTS = [{'Name': 'Ethernet - 001',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 3
          }]

# Force ownership of ports
FORCE_OWNERSHIP = True


class OSPFRoutingEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int, live_mode: bool):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True,
                         live_mode=live_mode)

    def populate_ospf_settings(self):
        """
        Populates global variable VELO_OSPF_SETTINGS missing values based on the provided values
        :return: None
        """
        # Get Device module from Edge Specific Profile
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get Segment ID based from VELO_OSPF_SETTINGS['Segment Name']
        for segment in device_module.data['segments']:
            if segment['segment']['name'] == VELO_OSPF_SETTINGS['Segment Name']:
                VELO_OSPF_SETTINGS['Segment ID'] = segment['segment']['segmentId']

        # Get VLAN ID and VLAN IP Address based on VELO_OSPF_SETTINGS['VLAN Name']
        for network in device_module.data['lan']['networks']:
            if network['name'] == VELO_OSPF_SETTINGS['VLAN Name']:
                VELO_OSPF_SETTINGS['VLAN ID'] = network['vlanId']
                VELO_OSPF_SETTINGS['VLAN IP Address'] = network['cidrIp']

        # Get Management IP
        VELO_OSPF_SETTINGS['Management IP'] = device_module.data['lan']['management']['cidrIp']

    def set_ospf_settings(self):
        """
        Sets Edges OSPF settings based on global variable VELO_OSPF_SETTINGS
        :return: None
        """
        # Bool flag to check if an update/is required on the Edge
        update_required = False

        # Get Device module from Edge Specific Profile
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get VELO_OSPF_SETTINGS['Segment ID'] based from VELO_OSPF_SETTINGS['Segment Name']
        for segment in device_module.data['segments']:
            if segment['segment']['name'] == VELO_OSPF_SETTINGS['Segment Name']:
                VELO_OSPF_SETTINGS['Segment ID'] = segment['segment']['segmentId']

        # CONFIGURE VLAN
        # Get VLAN based on VELO_OSPF_SETTINGS['VLAN Name']
        # by default it is set to Global Segment
        for network in device_module.data['lan']['networks']:
            if network['name'] == VELO_OSPF_SETTINGS['VLAN Name']:
                VELO_OSPF_SETTINGS['VLAN ID'] = network['vlanId']
                VELO_OSPF_SETTINGS['VLAN IP Address'] = network['cidrIp']

                # Once VLAN is found, check if OSPF is enabled
                if not network['ospf']['enabled']:
                    print(f"Enabling OSPF on VLAN: {VELO_OSPF_SETTINGS['VLAN Name']}")
                    network['ospf']['enabled'] = True
                    update_required = True

                if not network['ospf']['area'] == 0:
                    print(f"Setting OSPF Area to 0")
                    network['ospf']['area'] = 0
                    update_required = True

                if not network['ospf']['passiveInterface']:
                    print(f"Enabling OSPF Passive Interface")
                    network['ospf']['passiveInterface'] = True
                    update_required = True

        # INTERFACE SETTINGS
        # Get Interface based on VELO_OSPF_SETTINGS['Interface']
        for interface in device_module.data['routedInterfaces']:
            if interface['name'] == VELO_OSPF_SETTINGS['Interface Name']:
                # Verify Interface is Enabled
                if interface['disabled']:
                    print(f"Enabling Interface {VELO_OSPF_SETTINGS['Interface Name']}")
                    interface['disabled'] = False

                # Verify it is on the same segment as VELO_OSPF_SETTINGS['Segment Name']
                if not interface['segmentId'] == VELO_OSPF_SETTINGS['Segment ID']:
                    print(f"Setting Interface {VELO_OSPF_SETTINGS['Interface Name']} Segment to"
                          f" {VELO_OSPF_SETTINGS['Segment Name']}")
                    interface['segmentId'] = VELO_OSPF_SETTINGS['Segment ID']
                    update_required = True

                # Verify OSPF is enabled
                if not interface['ospf']['enabled']:
                    print(f"Enabling OSPF on Interface {VELO_OSPF_SETTINGS['Interface Name']}")
                    interface['ospf']['enabled'] = True
                    update_required = True

                # Verify OSPF Area
                if not interface['ospf']['area'] == [0]:
                    print(f"Setting OSPF Area to 0 on interface {VELO_OSPF_SETTINGS['Interface Name']}")
                    interface['ospf']['area'] = [0]
                    update_required = True

                # Verify Inbound Route Learning
                if not interface['ospf']['inboundRouteLearning']['defaultAction'] == 'LEARN':
                    print(f"Setting OSPF Inbound Route Learning Default Action to LEARN on "
                          f"Interface {VELO_OSPF_SETTINGS['Interface Name']}")
                    interface['inboundRouteLearning']['defaultAction'] = 'LEARN'
                    update_required = True

                # Verify Route Advertisement
                if not interface['ospf']['outboundRouteAdvertisement']['defaultAction'] == 'ADVERTISE':
                    print(f"Setting OSPF Outbound Route Advertisement Default Action to ADVERTISE on "
                          f"Interface {VELO_OSPF_SETTINGS['Interface Name']}")
                    interface['outboundRouteAdvertisement']['defaultAction'] = 'ADVERTISE'
                    update_required = True

                # TODO check Interface -> Addressing -> IP Address


# Object for Velocloud
EDGE: OSPFRoutingEdge

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
        # TODO change local_file to True once its all done
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

    ospf = IX_NETWORK.Vport.find().Protocols.find().Ospf
    IX_NETWORK.info('Starting OSPF Protocol...')
    ospf.Start()
    IX_NETWORK.info('OSPF Protocol started.')

    IX_NETWORK.info('Checking for OSPF Full Nbrs to equal to 1...')
    ospf_aggregated_stats = SESSION_ASSISTANT.StatViewAssistant(ViewName='OSPF Aggregated Statistics', Timeout=180)
    while True:
        try:
            while not ospf_aggregated_stats.CheckCondition(ColumnName='Full Nbrs.',
                                                           Comparator=StatViewAssistant.EQUAL,
                                                           ConditionValue=1,
                                                           Timeout=180):
                IX_NETWORK.info('Waiting for OSPF Full Nbrs. to equal 1...')
                time.sleep(10)
        except SyntaxError:
            continue
        except NotFoundError:
            print({'error': "OSPF Session Timeout"})
            return
        break

    IX_NETWORK.info('OSPF Full Nbrs equals to 1.')


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


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = OSPFRoutingEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0, live_mode=True)
    EDGE.populate_ospf_settings()
    print(VELO_OSPF_SETTINGS)


def get_ospf_neighbors():
    print(EDGE.LiveMode.get_ospf_neighbors())


def get_ospf_database():
    print(EDGE.LiveMode.get_ospf_database())


def verify_if_received_routes_match_ix_network(link_ids, adv_routes):
    received_ips = []

    # Create a list of dict with the link_id as key and adv_route as value based on parameters
    for link_id, adv_route in zip(link_ids, adv_routes):
        if adv_route == VELO_OSPF_SETTINGS['Management IP']:
            received_ips.append({link_id: adv_route})

    # Get the Learned LSA from Ixia
    learned_lsa = IX_NETWORK.Vport.find().Protocols.find().Ospf.Router.find().Interface.find().LearnedLsa.find()
    learned_lsa_ips = []
    for lsa in learned_lsa:
        if lsa.LsaType == 'external':
            learned_lsa_ips.append({lsa.LinkStateId: lsa.AdvRouterId})

    if learned_lsa_ips == received_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})
        print({'Velo': received_ips})
        print({'IxNetwork': learned_lsa_ips})


def verify_if_advertised_routes_match_ix_network(link_ids, adv_routes):
    advertised_ips = []

    # Get the Router Id from IxNetwork
    # Protocols -> OSPF -> "Ethernet - 001" -> "RID - 192.168.184.2" -> Router ID
    router = IX_NETWORK.Vport.find().Protocols.find().Ospf.Router.find()
    router_id = router.RouterId

    # Create a list of dict with the link_id as key and adv_route as value based on parameters
    # These values come from Velo OSPF Database
    for link_id, adv_route in zip(link_ids, adv_routes):
        if adv_route == router_id:
            advertised_ips.append({link_id: adv_route})

    # Get Route Ranges from IxNetwork
    # Protocols -> OSPF -> "Ethernet - 001" -> "RID - 192.168.184.2" -> RouteRanges
    route_ranges = router.RouteRange.find()

    # Grab each first route in route ranges and add routes based on the number of routes.
    # ex.   first route = '172.17.55.0' and number of routes 2
    #       second route = '172.17.56.0'
    # Will create a list of dict with the router_id being the value
    # ex.   [{172.17.55.0: 192.168.184.2}
    #           ...
    #            ...
    #       ]
    # These values come from IxNetwork
    route_ranges_ips = []
    for route in route_ranges:
        number_of_routes = route.NumberOfRoutes
        ip = ip_address(address=route.NetworkNumber)
        while number_of_routes > 0:
            route_ranges_ips.append({str(ip): router_id})
            ip = ip + 256
            number_of_routes -= 1

    # Verify if the list created from Velo and list created from IxNetwork match
    if route_ranges_ips == advertised_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})
        print({'Velo': advertised_ips})
        print({'IxNetwork': route_ranges_ips})


if __name__ == '__main__':
    start_ix_network()
    # verify_if_received_routes_match_ix_network(link_ids=[], adv_routes=[])
    verify_if_advertised_routes_match_ix_network(link_ids=[], adv_routes=[])
    stop_ix_network()