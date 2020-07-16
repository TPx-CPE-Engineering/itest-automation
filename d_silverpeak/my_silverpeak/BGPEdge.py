from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError
import json
import time

# Used in BGP Test Cases
# bgp_3.00_verify_neighbor_adjacency_advertised_received
# bgp_3.01_verify_md5_authentication
# bgp_3.02_verify_prepend_count
# bgp_3.03_verify_med

DEFAULT_BGP_PEER_IP = '192.168.131.99'

DEFAULT_BGP_INFORMATION = {
    'Config System': {
        'enable': True,                 # Enable BGP, default True
        'asn': 64514,                   # Autonomous System Number, default 64514
        'rtr_id': '192.168.131.1',      # Router ID, default 192.168.131.1
        'graceful_restart_en': False,   # Graceful Restart, default False
        'max_restart_time': 120,        # Max Restart Time, default 120
        'stale_path_time': 150,         # Stale Path Time, default 150
        'remote_as_path_advertise': False,      # AS Path Propagate, default False
        'redist_ospf': True,            # Redistribute OSPF Routes to BGP, default True
        'redist_ospf_filter': 0,        # Filter Tag, default 0
        'log_nbr_msgs': True            # default, True
    },
    'BGP Peers': [{
        DEFAULT_BGP_PEER_IP: {             # Default Neighbor 192.168.131.99
            'enable': True,             # Enable Peer, default True
            'self': DEFAULT_BGP_PEER_IP,   # Peer IP, default 192.168.131.99
            'remote_as': 64514,         # Peer ASN, default 64514
            'import_rtes': True,        # Enable Imports, default True
            'type': 'Branch',           # Peer Type, default Branch
            'loc_pref': 100,            # Local Preference, default 100
            'med': 0,                   # MED, default 0
            'as_prepend': 0,            # AS Prepend Count (0..10), default 0
            'next_hop_self': False,     # Next-Hop-Self, default False
            'in_med': 0,                # Input Metric, default 0
            'ka': 30,                   # Keep Alive Timer*, default 30
            'hold': 90,                 # Hold Timer*, default 90
                                        # * Timer changes only take effect when BGP session is reset. Admin Down, Up
                                        #   for changes to take effect immediately.
            'export_map': 4294967295,
            'password': ''              # MD5 Password, empty string to be disabled, default empty string/disabled
        }
    }]
}

# File Path where all IxNetwork configs live in
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'

# IP Address where IxNetwork Program (not chassis)
IX_NETWORK_IP = '10.255.20.7'


class BGPEdge(SPBaseEdge):
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
        response = self.api.post_bgp_config_system(applianceID=self.edge_id,
                                                   bgpConfigSystemData=json.dumps(bgp_config_sys))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error enabling BGP', 'data': response.data})
            return

        print({'error': None, 'message': 'BGP enabled successfully', 'data': response.data})

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
        response = self.api.post_bgp_config_system(applianceID=self.edge_id,
                                                   bgpConfigSystemData=json.dumps(bgp_config_sys))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error disabling BGP', 'data': response.data})
            return

        print({'error': None, 'message': 'BGP disabled successfully', 'data': response.data})

    def set_bgp_settings(self, bgp_settings):
        """
        Sets Edge's BGP Settings
        :param bgp_settings: bgp settings config, must match global DEFAULT_BGP_INFORMATION structure
        :return:
        """

        # Push BGP Config System
        response = self.api.post_bgp_config_system(applianceID=self.edge_id,
                                                   bgpConfigSystemData=json.dumps(bgp_settings['Config System']))
        # Check response status
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error setting BGP config system', 'data': response.data})
        else:
            print({'error': None, 'message': 'Setting BGP config system successful', 'data': response.data})

        # Set the BGP Peers Config
        # First Peer is the default Peer
        neighbors_config = bgp_settings['BGP Peers'][0]

        # Push BGP Peers config
        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(neighbors_config))
        # Check response status
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error setting BGP config neighbors', 'data': response.data})
        else:
            print({'error': None, 'message': 'Setting BGP config neighbors successful', 'data': response.data})

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

    def set_local_preference_on_bgp_peer(self, local_preference=100, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Sets Local Preference for a BGP Peer
        :param local_preference: <int> Local Preference for Peer, default 100
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """

        # Get BGP Peers configuration
        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        try:
            if bgp_config_neighbors[bgp_peer_ip]['loc_pref'] == local_preference:
                print({'error': None, 'message': f"Local Preference already set to {local_preference}."})
                return
        except KeyError:
            print({'error': f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.'})
            return

        # Set Local Preference
        bgp_config_neighbors[bgp_peer_ip]['loc_pref'] = local_preference

        # Push Call
        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        # Check Response Status Code
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error setting local preference','data': response.data})
            return
        else:
            print({'error': None, 'message': 'Local preference set successfully', 'data': response.data})

    def set_med_on_bgp_peer(self, med=0, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Sets MED for a BGP Peer
        :param med: <int> MED for Peer, default 0
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        try:
            if bgp_config_neighbors[bgp_peer_ip]['med'] == med:
                print({'error': None, 'message': f"MED already set to {med}."})
                return
        except KeyError:
            print({'error': f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.'})
            return

        # else
        bgp_config_neighbors[bgp_peer_ip]['med'] = med

        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print({'error': response.error, 'message': "Error setting MED", 'data': response.data})
            return
        else:
            print({'error': None, 'message': 'MED set successfully','data': response.data})


class Ixia:
    def __init__(self, ip_address=IX_NETWORK_IP, log_level=SessionAssistant.LOGLEVEL_INFO, clear_config=True):
        self.SessionAssistant = SessionAssistant(IpAddress=ip_address,
                                                 LogLevel=log_level,
                                                 ClearConfig=clear_config)
        self.IxNetwork = self.SessionAssistant.Ixnetwork
        self.PortMap = self.SessionAssistant.PortMapAssistant()

    def start_ix_network(self, config:str, vports:list, vports_force_ownership=True, config_local=True):
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

        # # Set DUT Port based on DUT property in global PORTS
        # dut_port_name = vports[0]['Name']
        # dut_port = self.IxNetwork.Vport.find(Name=dut_port_name)
        #
        # # First get BGP
        # bgp = dut_port.Protocols.find().Bgp

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