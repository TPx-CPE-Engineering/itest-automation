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
VELO_OSPF_SETTINGS = {'Segment Name': 'Global Segment',  # CHANGE Segment Name if need to
                      'Segment ID': None,  # Will get populated in populate_ospf_settings()
                      'VLAN Name': 'Corporate',  # CHANGE VLAN Name if need too
                      'VLAN ID': None,  # Will get populated in populate_ospf_settings()
                      'VLAN IP Address': None,
                      'Interface Name': 'GE2',  # CHANGE Interface if need too
                      'Management IP': None  # Will get populated in populate_ospf_settings()
                      }

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'
IX_NET_CONFIG_FILE = 'ospf_2_01_verify_md5_authentication.ixncfg'
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

        # Perform API Call if update is required
        if update_required:
            # Setup API parameter
            param = ConfigurationUpdateConfigurationModule(id=device_module.id,
                                                           enterpriseId=self.enterprise_id,
                                                           update=device_module)
            # Execute API call
            res = EDGE.api.configurationUpdateConfigurationModule(param)

            # Print API response
            print(res)

    def enable_ospf_md5_auth(self, key_id, password):
        """
        Enables OSPF MD5 Authentication for VELO_OSPF_SETTINGS['Interface Name'] and sets the Key ID and Password

        Device -> Interface Settings -> Edit VELO_OSPF_SETTINGS['Interface Name'] -> OSPF -> toggle advance ospf
        settings -> Check Enable MD5 Authentication, Set Key ID, Set Password
        :param key_id: <int> Key ID for MD5 Authentication, must be between 1 - 255
        :param password: <str> Password for MD5 Authentication
        :return: None
        """
        if not key_id >= 1 or not key_id <= 255:
            print('Arg: key_id, Must be between 1 - 255')
            return

        # Get Device Module from Edge
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # bool flag to check if an update api call is needed
        update_required = False

        # INTERFACE SETTINGS
        # Get Interface based on VELO_OSPF_SETTINGS['Interface Name']
        for interface in device_module.data['routedInterfaces']:
            if interface['name'] == VELO_OSPF_SETTINGS['Interface Name']:

                # Enable Authentication on Interface if not enabled
                if not interface['ospf']['authentication']:
                    interface['ospf']['authentication'] = True
                    update_required = True

                # Set Key ID
                if not interface['ospf']['authId'] == key_id:
                    interface['ospf']['authId'] = key_id
                    update_required = True

                # Set Password
                if not interface['ospf']['authPassphrase'] == password:
                    interface['ospf']['authPassphrase'] = password
                    update_required = True

                # Note: there is a md5Authentication key although it does not seem to change when enabling MD5 Auth
                # within the GUI

        if update_required:
            # Setup API parameter
            param = ConfigurationUpdateConfigurationModule(id=device_module.id,
                                                           enterpriseId=self.enterprise_id,
                                                           update=ConfigurationModule(data=device_module.data))
            # Execute API call
            res = EDGE.api.configurationUpdateConfigurationModule(param)

            # Print API response
            print(res)
        else:
            print({'error': None, 'rows': 0})

    def disable_ospf_md5_auth(self):
        """
        Disables OSPF MD5 Authentication for VELO_OSPF_SETTINGS['Interface Name'] and prints API Call results

        Device -> Interface Settings -> Edit VELO_OSPF_SETTINGS['Interface Name'] -> OSPF -> toggle advance ospf
        settings -> Uncheck Enable MD5 Authentication
        :return: None
        """
        device_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # bool flag to check if an update api call is needed
        update_required = False

        # INTERFACE SETTINGS
        # Get Interface based on VELO_OSPF_SETTINGS['Interface Name']
        for interface in device_module.data['routedInterfaces']:
            if interface['name'] == VELO_OSPF_SETTINGS['Interface Name']:

                # Disable Authentication on Interface if enabled
                if interface['ospf']['authentication']:
                    interface['ospf']['authentication'] = False
                    update_required = True

                # Note: there is a md5Authentication key although it does not seem to change when enabling MD5 Auth
                # within the GUI

        if update_required:
            # Setup API parameter
            param = ConfigurationUpdateConfigurationModule(id=device_module.id,
                                                           enterpriseId=self.enterprise_id,
                                                           update=ConfigurationModule(data=device_module.data))
            # Execute API call
            res = EDGE.api.configurationUpdateConfigurationModule(param)

            # Print API response
            print(res)
        else:
            print({'error': None, 'rows': 0})


# Object for Velocloud
EDGE: OSPFRoutingEdge

# Objects for Ixia IxNetwork
SESSION_ASSISTANT: SessionAssistant
IX_NETWORK: SessionAssistant.Ixnetwork
PORT_MAP: SessionAssistant.PortMapAssistant


# noinspection PyTypeChecker
def start_ix_network(enable_ospf_md5=False, key_id=1, password='maule123'):
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

    #############################################
    # Enable OSPF MD5 Authentication on Interface
    interface = ospf.Router.find().Interface.find()

    if enable_ospf_md5:
        # Enable MD5 Authentication for the Interface
        if not interface.AuthenticationMethods == 'md5':
            IX_NETWORK.info('Setting OSPF Interface Authentication to MD5 Method...')
            interface.AuthenticationMethods = 'md5'

        # Set the MD5 Key ID
        if not interface.Md5AuthenticationKeyId == key_id:
            IX_NETWORK.info(f'Setting OSPF Interface Authentication key to {key_id}...')
            interface.Md5AuthenticationKeyId = key_id

        # Set the MD5 password
        if not interface.Md5AuthenticationKey == password:
            IX_NETWORK.info(f'Setting OSPF Interface Authentication password to f{password}...')
            interface.Md5AuthenticationKey = password

    else:
        # Disable MD5 Authentication on Interface
        IX_NETWORK.info('Setting OSPF Interface Authentication to null')
        interface.AuthenticationMethods = 'null'
    ################################################

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


def stop_ix_network(disconnect_ports=True):
    # Stop protocols
    IX_NETWORK.info('Stopping protocols...')
    IX_NETWORK.StopAllProtocols()
    IX_NETWORK.info('Protocols stopped.')

    # Disconnect PORTS
    if disconnect_ports:
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


def disable_ospf_md5_auth():
    EDGE.disable_ospf_md5_auth()


def enable_ospf_md5_auth(key_id=0, password='maule123'):
    EDGE.enable_ospf_md5_auth(key_id=key_id, password=password)


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    EDGE.enable_ospf_md5_auth(key_id=1, password='maule123')
    # EDGE.disable_ospf_md5_auth()