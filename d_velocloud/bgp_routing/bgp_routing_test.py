from my_velocloud.BaseEdge import BaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time

# Hardcoded values for test. Update if need to.
BGP_SETTINGS = {'Segment Name': 'Global Segment',
                'BGP Enabled': True,
                'Local ASN': '65535',
                'Neighbor IP': '192.168.144.2',
                'Neighbor ASN': '65535'
                }
# Ixia Settings
# Config File
# IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\AppData\\Local\\Ixia\\IxNetwork\\AutomationConfigs\\'
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\Configs\\'
IX_NET_CONFIG_FILE = 'juan_ixnetwork8_50_test2.ixncfg'
FULL_CONFIG = IX_NET_CONFIG_FILE_BASE + IX_NET_CONFIG_FILE

# Chassis IP
IX_NET_CHASSIS_IP = '10.255.224.70'

PORTS = [{'Name': 'Single 540 LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 1
          },
         {'Name': '520HA LAN',
          'Chassis IP': IX_NET_CHASSIS_IP,
          'Card': 3,
          'Port': 3
          }]

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
        bgp_settings_segment = self.get_segment_from_module(segment_name=BGP_SETTINGS['Segment Name'],
                                                            module=device_module)
        if not bgp_settings_segment:
            print({'error': f"No Configure Segment: {BGP_SETTINGS['Segment Name']} found."})
            exit(-1)

        # Within BGP_SETTINGS['Segment Name'] check for the rest of BGP Settings
        # Check #2 BGP_SETTINGS['BGP Enabled']
        if not bgp_settings_segment['bgp']['enabled']:
            print({'error': f"BGP Enabled is: {bgp_settings_segment['bgp']['enabled']}. "
                            f"Expecting: {BGP_SETTINGS['BGP Enabled']}."})
            exit(-1)

        # Check #3 BGP_SETTINGS['Local ASN']
        if not bgp_settings_segment['bgp']['ASN'] == BGP_SETTINGS['Local ASN']:
            print({'error': f"Local ASN is: {bgp_settings_segment['bgp']['ASN']}. "
                            f"Expecting: {BGP_SETTINGS['Local ASN']}."})
            exit(-1)

        # Check #4 BGP_SETTINGS['Neighbor IP']
        # Check #5 BGP_SETTINGS['Neighbor ASN']
        check_pass = False
        for neighbor in bgp_settings_segment['bgp']['neighbors']:
            if neighbor['neighborIp'] == BGP_SETTINGS['Neighbor IP'] and \
                    neighbor['neighborAS'] == BGP_SETTINGS['Neighbor ASN']:
                check_pass = True
                break

        if not check_pass:
            print({'error': f"No Neighbor IP: {BGP_SETTINGS['Neighbor IP']} with ASN: "
                            f"{BGP_SETTINGS['Neighbor ASN']} found."})
            exit(-1)

        print({'error': None})


# Object for Velocloud
EDGE: BGPRoutingEdge

# Objects for Ixia IxNetwork
SESSION_ASSISTANT: SessionAssistant
IX_NETWORK: SessionAssistant.Ixnetwork


def load_and_start_ix_network_config():
    # Initiate IxNetwork session
    global SESSION_ASSISTANT, IX_NETWORK

    # Initiate Session
    SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=True)

    # Get IxNetwork object from Session
    IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Load Config
    IX_NETWORK.info('Loading config...')
    try:
        IX_NETWORK.LoadConfig(Files(file_path=FULL_CONFIG, local_file=False))
    except BadRequestError as e:
        print({'error': f"{e.message}"})
        exit(-1)
    IX_NETWORK.info('Config loaded.')

    port_map = SESSION_ASSISTANT.PortMapAssistant()

    # Connect every port in PORTS
    for port in PORTS:
        port_map.Map(IpAddress=port['Chassis IP'],
                     CardId=port['Card'],
                     PortId=port['Port'],
                     Name=port['Name'])

    IX_NETWORK.info('Connecting to ports...')
    port_map.Connect(ForceOwnership=FORCE_OWNERSHIP)
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

    while not bgp_aggregated_stats.CheckCondition(ColumnName='Sess. Up',
                                                  Comparator=StatViewAssistant.EQUAL,
                                                  ConditionValue=1):
        IX_NETWORK.info('Waiting for BGP Session Up to equal 1...')
        time.sleep(10)

    IX_NETWORK.info('BGP Session Up.')

    # Apply traffic
    IX_NETWORK.info('Applying traffic...')
    IX_NETWORK.Traffic.Apply()
    IX_NETWORK.Traffic.StartStatelessTrafficBlocking()
    time.sleep(60)

    # Stop traffic
    IX_NETWORK.Traffic.StopStatelessTrafficBlocking()

    # Stop protocols
    IX_NETWORK.info('Stopping protocols...')
    IX_NETWORK.StopAllProtocols()
    IX_NETWORK.info('Protocols stopped.')

    # Disconnect PORTS
    IX_NETWORK.info('Disconnecting ports...')
    port_map.Disconnect()
    IX_NETWORK.info('Port disconnected.')


def stop_ix_network_config():

    # Connect to Initiated IxNetwork session

    # Stop Test
    print('todo')


def check_bgp_settings():
    EDGE.check_bgp_settings()


def get_bgp_neighbor_received_routes():
    print(EDGE.LiveMode.get_bgp_neighbor_received_routes(segment_id=0, neighbor_ip='192.168.144.2'))


def get_bgp_neighbor_advertised_routes():
    print(EDGE.LiveMode.get_bgp_neighbor_advertised_routes(segment_id=0, neighbor_ip='192.168.144.2'))


def get_bgp_summary():
    print(EDGE.LiveMode.get_bgp_summary())


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0)


if __name__ == '__main__':
    # create_edge(edge_id=3, enterprise_id=1)
    # check_bgp_settings()
    load_and_start_ix_network_config()
    # new_new()
