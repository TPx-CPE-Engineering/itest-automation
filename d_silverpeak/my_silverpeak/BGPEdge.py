from my_silverpeak.base_edge import SPBaseEdge
from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import json
import time

# Used in BGP Test Cases
# bgp_3.00_verify_neighbor_adjacency_advertised_received
# bgp_3.01_verify_md5_authentication
# bgp_3.02_verify_prepend_count
# bgp_3.03_verify_med
# bgp_3.04_verify_local_preference

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
            'enable': True,             # Admin Status(True=UP Admin Status, False=Down Admin Status), default True
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

        # Check if BGP already is enabled
        if bgp_config_sys['enable']:
            print({'error': None, 'message': 'BGP already enabled'})
            return
        else:
            # enable BGP
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

        # Check if BGP already disabled
        if not bgp_config_sys['enable']:
            print({'error': None, 'message': 'BGP already disabled'})
            return
        else:
            # disable BGP
            bgp_config_sys['enable'] = False

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
        # neighbors_state = []
        # for i in range(0, 100):
        #     while True:
        #         bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)
        #         try:
        #             for neighbor in bgp_state.data['neighbor']['neighborState']:
        #                 neighbors_state.append({'neighbor': neighbor['peer_ip'],
        #                                         'state': neighbor['peer_state_str']})
        #         except KeyError:
        #             time.sleep(15)
        #             continue
        #         break
        #
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

    def set_keep_alive_timer_on_bgp_peer(self, keep_alive_timer=0, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Sets Keep Alive Timer for a BGP Peer
        :param keep_alive_timer: <int> Keep Alive for BGP Peer, default 0
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        try:
            if bgp_config_neighbors[bgp_peer_ip]['ka'] == keep_alive_timer:
                print({'error': None, 'message': f"Keep Alive Timer already set to {keep_alive_timer}."})
                return
        except KeyError:
            print({'error': f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.'})
            return

        # else
        bgp_config_neighbors[bgp_peer_ip]['ka'] = keep_alive_timer

        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print({'error': response.error, 'message': "Error setting Keep Alive Timer", 'data': response.data})
            return
        else:
            print({'error': None, 'message': 'Keep Alive Timer set successfully','data': response.data})

    def set_hold_timer_on_bgp_peer(self, hold_timer=0, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Sets Hold Timer for a BGP Peer
        :param hold_timer: <int> Hold Timer for BGP Peer, default 0
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        try:
            if bgp_config_neighbors[bgp_peer_ip]['hold'] == hold_timer:
                print({'error': None, 'message': f"Hold Timer already set to {hold_timer}."})
                return
        except KeyError:
            print({'error': f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.'})
            return

        # else
        bgp_config_neighbors[bgp_peer_ip]['hold'] = hold_timer

        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print({'error': response.error, 'message': "Error setting Hold Timer", 'data': response.data})
            return
        else:
            print({'error': None, 'message': 'Hold Timer set successfully','data': response.data})

    def set_as_prepend_count_on_bgp_peer(self, as_prepend_count=0, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Enables AS Prepend Count for a BGP Peer
        :param as_prepend_count: <int> 0-10, default 0
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """

        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data
        try:
            if bgp_config_neighbors[bgp_peer_ip]['as_prepend'] == as_prepend_count:
                print({'error': None, 'message': f'AS Prepend already set to {as_prepend_count}'})
                return
        except KeyError:
            print({'error': f'BGP Peer IP: {bgp_peer_ip} is not found. Confirm if Peer is in Edge\'s BGP Peers.'})
            return
        # else
        bgp_config_neighbors[bgp_peer_ip]['as_prepend'] = as_prepend_count

        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))

        if not response.status_code == 200:
            print({'error': response.error, 'message': "Error setting AS Prepend Count", 'data': response.data})
            return
        else:
            print({'error': None, 'message': 'AS Prepend Count set successfully','data': response.data})

    def get_bgp_route_table(self):
        bgp_state = self.api.get_bgp_state(applianceID=self.edge_id)

        print(bgp_state.data['rttable'])

    def enable_bgp_md5_auth(self, password, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Enables MD5 Auth on BGP Peer with passed password
        :param password: <str> Password for MD5 Authentication
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """
        # Get BGP neighbors settings
        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        # Enable BGP MD5 Auth on the neighbor ip by setting the password
        # If password already set and matches argument password then don't call api
        if bgp_config_neighbors[bgp_peer_ip]['password'] == password:
            print({'error': None, 'message': f'BGP MD5 Auth password already set to {password}'})
            return

        # Else password is not set or does not match so set it
        bgp_config_neighbors[bgp_peer_ip]['password'] = password
        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error setting BGP MD5 Auth', 'data': response.data})
        else:
            print({'error': None, 'message': 'BGP MD5 Auth set successfully', 'data': response.data})

    def disable_bgp_md5_auth(self, bgp_peer_ip=DEFAULT_BGP_PEER_IP):
        """
        Disables MD5 Auth on SP_BGP_SETTINGS[BGP Peer]
        :param bgp_peer_ip: <str> IP of BGP Peer, default DEFAULT_BGP_PEER_IP
        :return: None
        """
        # Get BGP neighbors settings
        bgp_config_neighbors = self.api.get_bgp_config_neighbor(applianceID=self.edge_id).data

        # Disable BGP MD5 Auth on the neighbor ip by setting the password to an empty string
        # If password already empty then don't call api
        if bgp_config_neighbors[bgp_peer_ip]['password'] == "":
            print({'error': None, 'message': 'BGP MD5 already disabled'})
            return

        # Else set password to empty and call api
        bgp_config_neighbors[bgp_peer_ip]['password'] = ""
        response = self.api.post_bgp_config_neighbor(applianceID=self.edge_id,
                                                     bgpConfigNeighborData=json.dumps(bgp_config_neighbors))
        if not response.status_code == 200:
            print({'error': response.error, 'message': 'Error disabling BGP MD5 authentication', 'data': response.data})
        else:
            print({'error': None, 'message': 'Disabled BGP MD5 Auth successfully', 'data': response.data})


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