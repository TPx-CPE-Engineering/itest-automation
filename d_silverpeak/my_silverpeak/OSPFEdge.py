from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import json
import time

# Used in OSPF Test Cases
# ospf_2.00_verify_neighbor_adjacency_advertised_received

DEFAULT_OSPF_PEER_IP = '192.168.131.99'

DEFAULT_OSPF_INTERFACE = 'lan0'

DEFAULT_OSPF_INFORMATION = {
    'Config System': {
        "enable": True,                     # Enable OSPF, default True
        "routerId": "192.168.131.1",        # Router ID, default 192.168.131.1
        "redistBgp": False,                 # Redistribute BGP routes to OSPF, default False
        "bgpRedistMetricType": 2,               # Metric Type, default 2 aka 'E2'
        "bgpRedistMetric": 0,                   # Metric, default 0
        "bgpRedistTag": 0,                      # Tag, default 0
        "redistSubnetShare": True,          # Redistribute Silver Peak peers routes to OSPF, default True
        "subnetShareRedistMetricType": 2,       # Metric Type, default 2 aka 'E2'
        "subnetShareRedistMetric": 0,           # Metric, default 0
        "subnetShareRedistTag": 0,              # Tag, default 0
        "redistLocal": True,                # Redistribute local routes to OSPF, default True
        "localRedistMetricType": 2,             # Metric Type, default 2 aka 'E2'
        "localRedistMetric": 0,                 # Metric, default 0
        "localRedistTag": 0                     # Tag, default 0
    },
    'Interfaces': {
        DEFAULT_OSPF_INTERFACE: {
            "self": DEFAULT_OSPF_INTERFACE,             # Interface, default lan0
            "area": "0.0.0.0",          # Area ID, default 0.0.0.0
            "cost": 1,                  # Cost, default 1
            "priority": 1,              # Priority, default 1
            "adminStatus": True,        # Admin Status, (True = UP | False = DOWN), default True (UP)
            "helloInterval": 10,        # Hello Interval (1..65535) Sec, default 10
            "deadInterval": 40,         # Dead Interval (1..65535) Sec, default 40
            "transmitDelay": 1,         # Transmit Delay (1..450) Sec, default 1
            "retransmitInterval": 4,    # Retransmit Interval (1..65535) Sec, default 4
            "authType": "None",         # Authentication, default None
            "authKey": "",              # Authentication key if authType set to 'Text', default empty
            "md5Key": 0,                # MD5 Key if authType set to 'MD5', default 0
            "md5Password": "",          # MD5 Password if authType set to 'MD5', default empty
            "comment": "Config set by iTest"    # Comment
        }
    }
}

# File Path where all IxNetwork configs live in
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'

# IP Address where IxNetwork Program (not chassis)
IX_NETWORK_IP = '10.255.20.7'


class OSPFEdge(SPBaseEdge):
    def __init__(self, edge_id: str, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)

    def set_ospf_settings_to_default(self):
        """
        Sets OSPF System Config and Interfaces to DEFAULT_OSPF_INFORMATION
        :return: None
        """

        # Set System Config to DEFAULT_OSPF_INFORMATION['Config System']
        default_ospf_config_system = json.dumps(DEFAULT_OSPF_INFORMATION['Config System'])
        response = self.api.post_ospf_config_system(applianceID=self.edge_id,
                                                    ospfConfigSystemData=default_ospf_config_system)
        print(response)

        # Set Interface Config to DEFAULT_OSPF_INFORMATION['Interfaces']
        default_ospf_interface = json.dumps(DEFAULT_OSPF_INFORMATION['Interfaces'])
        response = self.api.post_ospf_interfaces(applianceID=self.edge_id,
                                                 interfaceConfigData=default_ospf_interface)
        print(response)

    def enable_ospf(self):
        """
        Enables OSPF on Edge
        :return: None
        """
        # Get existing OSPF config system data
        ospf_config_sys = self.api.get_ospf_config_system(applianceID=self.edge_id).data

        # Check if OSPF already is enabled
        if ospf_config_sys['enable']:
            print({'error': None, 'message': 'OSPF already enabled'})
            return
        else:
            # enable BGP
            ospf_config_sys['enable'] = True

        # Post change
        response = self.api.post_ospf_config_system(applianceID=self.edge_id,
                                                    ospfConfigSystemData=json.dumps(ospf_config_sys))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error enabling OSPF', 'data': response.data})
            return

        print({'error': None, 'message': 'OSPF enabled successfully', 'data': response.data})

    def disable_ospf(self):
        """
        Disables OSPF on Edge
        :return: None
        """
        # Get existing OSPF config system data
        ospf_config_sys = self.api.get_ospf_config_system(applianceID=self.edge_id).data

        # Check if BGP already disabled
        if not ospf_config_sys['enable']:
            print({'error': None, 'message': 'OSPF already disabled'})
            return
        else:
            # Set BGP to disable
            ospf_config_sys['enable'] = False

        # Post change
        response = self.api.post_ospf_config_system(applianceID=self.edge_id,
                                                    ospfConfigSystemData=json.dumps(ospf_config_sys))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error disabling OSPF', 'data': response.data})
            return

        print({'error': None, 'message': 'OSPF disabled successfully', 'data': response.data})

    def disable_ospf_md5_auth(self):
        """
        Disables OSPF MD5 Authentication on DEFAULT OSPF INTERFACE
        :return: None
        """

        # Get existing OSPF interfaces data
        ospf_interfaces = self.api.get_ospf_interfaces(applianceID=self.edge_id).data

        # Check if MD5 Auth is already disabled
        if ospf_interfaces[DEFAULT_OSPF_INTERFACE]['authType'] == "None":
            print({'error': None, 'message': f'OSPF MD5 Auth already disabled'})
            return

        # If not already disabled, then disable
        ospf_interfaces[DEFAULT_OSPF_INTERFACE]['authType'] = "None"

        # Post update
        response = self.api.post_ospf_interfaces(applianceID=self.edge_id,
                                                 interfaceConfigData=json.dumps(ospf_interfaces))

        if not response.status_code == 200:
            print({'error': response.error,
                   'message': "Error disabling OSPF MD5 Auth",
                   'data': response.data})
        else:
            print({'error': None,
                   'message': "Disabled OSPF MD5 Auth successfully",
                   'data': response.data})

    def enable_ospf_md5_auth(self, md5_password, md5_key):
        """
        Enables OSPF MD5 Authentication on DEFAULT OSPF INTERFACE
        :param md5_password: md5 password for interface
        :param md5_key: md5 key for interface
        :return: None
        """

        # Get existing OSPF interfaces data
        ospf_interfaces = self.api.get_ospf_interfaces(applianceID=self.edge_id).data

        # Check if OSPF is enabled with the same md5 password and md5 key
        if ospf_interfaces[DEFAULT_OSPF_INTERFACE]['authType'] == 'MD5' and \
                ospf_interfaces[DEFAULT_OSPF_INTERFACE]['md5Key'] == md5_key and \
                ospf_interfaces[DEFAULT_OSPF_INTERFACE]['md5Password'] == md5_password:
            print({'error': None, 'message': f'OSPF MD5 Auth already enabled'})
            return

        # If not enabled, then enable and set passwords
        ospf_interfaces[DEFAULT_OSPF_INTERFACE]['authType'] = 'MD5'
        ospf_interfaces[DEFAULT_OSPF_INTERFACE]['md5Key'] = md5_key
        ospf_interfaces[DEFAULT_OSPF_INTERFACE]['md5Password'] = md5_password

        # Post update
        response = self.api.post_ospf_interfaces(applianceID=self.edge_id,
                                                 interfaceConfigData=json.dumps(ospf_interfaces))

        if not response.status_code == 200:
            print({'error': response.error,
                   'message': "Error enabling OSPF MD5 Auth",
                   'data': response.data})
        else:
            print({'error': None,
                   'message': f"Enabled OSPF MD5 Auth with password: '{md5_password}' and key '{md5_key}' successfully",
                   'data': response.data})


class Ixia:
    def __init__(self, ip_address=IX_NETWORK_IP, log_level=SessionAssistant.LOGLEVEL_INFO, clear_config=True):
        self.SessionAssistant = SessionAssistant(IpAddress=ip_address,
                                                 LogLevel=log_level,
                                                 ClearConfig=clear_config)
        self.IxNetwork = self.SessionAssistant.Ixnetwork
        self.PortMap = self.SessionAssistant.PortMapAssistant()

    def start_ix_network(self, config:str, vports:list, vports_force_ownership=True, config_local=True,
                         enable_md5=False, md5_password=None, md5_key=None):
        # Load Config
        self.IxNetwork.info(f'Loading config: {config}...')
        try:
            self.IxNetwork.LoadConfig(Files(file_path=IX_NET_CONFIG_FILE_BASE + config,
                                            local_file=config_local))
        except BadRequestError as e:
            print({'error': f"{e.message}"})
            exit(-1)
        self.IxNetwork.info('Config loaded.')

        # Connect every port in vports
        for port in vports:
            self.PortMap.Map(IpAddress=port['Chassis IP'],
                             CardId=port['Card'],
                             PortId=port['Port'],
                             Name=port['Name'])

        self.IxNetwork.info('Connecting to ports...')
        self.PortMap.Connect(ForceOwnership=vports_force_ownership)
        self.IxNetwork.info('Ports connected.')

        # Get Default Vport Name, Default will be first in list
        vport_name = vports[0]['Name']
        vport = self.IxNetwork.Vport.find(Name=vport_name)

        # Get OSPF Protocol
        ospf = vport.Protocols.find().Ospf
        # Get OSPF interface
        ospf_interface = ospf.Router.find().Interface.find()

        # Enable MD5 Auth in interface
        if enable_md5:
            if not ospf_interface.AuthenticationMethods == 'md5':
                self.IxNetwork.info('Setting OSPF Interface Authentication Method to \'md5\'.')
                ospf_interface.AuthenticationMethods = 'md5'

            if not ospf_interface.Md5AuthenticationKey == md5_password:
                self.IxNetwork.info(f"Setting OSPF Interface MD5 password to \'{md5_password}\'")
                ospf_interface.Md5AuthenticationKey = md5_password

            if not ospf_interface.Md5AuthenticationKeyId == md5_key:
                self.IxNetwork.info(f'Setting OSPF Interface Authentication key to {md5_key}...')
                ospf_interface.Md5AuthenticationKeyId = md5_key
        else:
            if not ospf_interface.AuthenticationMethods == 'null':
                self.IxNetwork.info('Setting OSPF Interface Authentication Method to null')
                ospf_interface.AuthenticationMethods = 'null'

        # Start protocols
        self.IxNetwork.info('Starting protocols...')
        self.IxNetwork.StartAllProtocols()
        self.IxNetwork.info('Protocols have started.')

        # Wait until Full Nbrs is 1
        self.IxNetwork.info('Checking for OSPF Full Nbrs equal 1...')
        ospf_aggregated_stats = self.SessionAssistant.StatViewAssistant(ViewName='OSPF Aggregated Statistics',
                                                                        Timeout=180)

        while True:
            try:
                while not ospf_aggregated_stats.CheckCondition(ColumnName='Full Nbrs.',
                                                               Comparator=StatViewAssistant.EQUAL,
                                                               ConditionValue=1,
                                                               Timeout=120):
                    self.IxNetwork.info('Waiting for OSPF Full Nbrs to equal 1...')
                    time.sleep(10)
            except SyntaxError:
                continue
            except NotFoundError:
                print({'error': 'OSPF Session Timeout'})
                return
            break

        self.IxNetwork.info('OSPF Full Nbrs equals to 1.')

    def stop_ix_network(self, port_map_disconnect=True):
        # Stopping All Protocols
        self.IxNetwork.info('Stopping all protocols...')
        self.IxNetwork.StopAllProtocols()
        self.IxNetwork.info('Protocols all stopped.')

        # Disconnect PORTS
        if port_map_disconnect:
            self.IxNetwork.info('Disconnecting ports...')
            self.PortMap.Disconnect()
            self.IxNetwork.info('Port disconnected.')