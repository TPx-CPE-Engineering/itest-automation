from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import json
import time

# Used in OSPF Test Cases
# ospf_2.00_verify_neighbor_adjacency_advertised_received

DEFAULT_OSPF_PEER_IP = '192.168.131.99'

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
    'Interfaces': [{
        'lan0': {
            "self": "lan0",             # Interface, default lan0
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
    }]
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


class Ixia:
    def __init__(self, ip_address=IX_NETWORK_IP, log_level=SessionAssistant.LOGLEVEL_INFO, clear_config=True):
        self.SessionAssistant = SessionAssistant(IpAddress=ip_address,
                                                 LogLevel=log_level,
                                                 ClearConfig=clear_config)
        self.IxNetwork = self.SessionAssistant.Ixnetwork
        self.PortMap = self.SessionAssistant.PortMapAssistant()

    def start_ix_network(self, config:str, vports:list, vports_force_ownership=True, config_local=True,
                         enable_md5=False, md5_password=None, hold_timer=None):
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

        # Set up IPv4 Peers Neighbors
        # First get BGP
        bgp = vport.Protocols.find().Bgp
        # Get BGPs Neighbor object
        neighbor = bgp.NeighborRange.find()

        # Enable BGP MD5 Auth on NeighborRange
        if enable_md5:
            if not neighbor.Authentication == 'md5':
                self.IxNetwork.info('Setting BGP NeighborRange Authentication to \'md5\'.')
                neighbor.Authentication = 'md5'

            if not neighbor.Md5Key == md5_password:
                self.IxNetwork.info(f"Setting BGP NeighborRange MD5 password to \'{md5_password}\'")
                neighbor.Md5Key = md5_password
        else:
            if not neighbor.Authentication == 'null':
                self.IxNetwork.info('Setting BGP NeighborRange Authentication to null')
                neighbor.Authentication = 'null'

        if hold_timer:
            self.IxNetwork.info(f'Setting BGP NeighborRange Hold Timer to \'{hold_timer}\'.')
            neighbor.HoldTimer = hold_timer

        # Start protocols
        self.IxNetwork.info('Starting protocols...')
        self.IxNetwork.StartAllProtocols()
        # self.IxNetwork.info('Starting BGP Protocol...')
        # bgp.Start()
        # time.sleep(10)
        # self.IxNetwork.info('BGP Protocol started.')
        self.IxNetwork.info('Protocols have started.')

        # Wait until Sess. Up is 1
        self.IxNetwork.info('Checking for BGP Session Up...')
        bgp_aggregated_stats = self.SessionAssistant.StatViewAssistant(ViewName='BGP Aggregated Statistics',
                                                                       Timeout=180)

        while True:
            try:
                while not bgp_aggregated_stats.CheckCondition(ColumnName='Sess. Up',
                                                              Comparator=StatViewAssistant.EQUAL,
                                                              ConditionValue=1,
                                                              Timeout=120):
                    self.IxNetwork.info('Waiting for BGP Session Up to equal 1...')
                    time.sleep(10)
            except SyntaxError:
                continue
            except NotFoundError:
                print({'error': 'BGP Session Timeout'})
                return
            break

        self.IxNetwork.info('BGP Session Up.')

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