from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import time


# File Path where all IxNetwork configs live in
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'

# IP Address where IxNetwork Program (not chassis)
IX_NETWORK_IP = '127.0.0.1'

# VPorts
PORTS = [{'Name': 'Ethernet - 001',
          'Chassis IP': '10.255.224.70',
          'Card': 3,
          'Port': 3
          }]


class IxNetwork:
    def __init__(self,
                 ip_address=IX_NETWORK_IP,
                 log_level=SessionAssistant.LOGLEVEL_INFO,
                 clear_config=True):
        self.SessionAssistant = SessionAssistant(IpAddress=ip_address,
                                                 LogLevel=log_level,
                                                 ClearConfig=clear_config)
        self.IxNetwork = self.SessionAssistant.Ixnetwork
        self.PortMap = self.SessionAssistant.PortMapAssistant()

    def load_config(self, config, config_local=True):
        """
        Load configuration file to Ix Network
        :param config: config file name
        :param config_local: Is config local or not
        :return: None
        """
        # Load Config
        self.IxNetwork.info(f'Loading config: {config}...')
        try:
            self.IxNetwork.LoadConfig(Files(file_path=IX_NET_CONFIG_FILE_BASE + config,
                                            local_file=config_local))
            time.sleep(10)
            self.IxNetwork.info('Config loaded.')
        except BadRequestError as e:
            print({'error': f"{e.message}"})
            exit(-1)

    def connect_vport(self, vport_name='DUT Edge'):
        """
        Connect and wait until vport is connected
        :param vport_name: Name of Vport
        :return: Vport
        """

        self.IxNetwork.info(f'Connecting vport \'{vport_name}\'...')
        vport = self.IxNetwork.Vport.find(Name='DUT Edge')

        while True:
            if not vport.IsConnected:
                time.sleep(3)
                vport.refresh()
            else:
                self.IxNetwork.info(f'\'{vport_name}\' is Connected.')
                return vport

    def start_bgp_ix_network(self,
                             config: str,
                             config_local=True,
                             enable_md5=False,
                             md5_password=None,
                             hold_timer=None,
                             ipv4_address=None,
                             ipv4_mask_width=None,
                             ipv4_gateway=None):

        self.load_config(config, config_local)
        vport = self.connect_vport(vport_name='DUT Edge')

        # Adjust Interface IP
        ipv4_interface = vport.Interface.find().Ipv4.find()
        ipv4_interface.Gateway = ipv4_gateway
        ipv4_interface.Ip = ipv4_address
        ipv4_interface.MaskWidth = ipv4_mask_width

        # Adjust BGP Protocol
        bgp = vport.Protocols.find().Bgp

        bgp_neighbor_range = bgp.NeighborRange.find()
        bgp_neighbor_range.BgpId = ipv4_address
        bgp_neighbor_range.DutIpAddress = ipv4_gateway
        bgp_neighbor_range.LocalAsNumber = 65535
        bgp_neighbor_range.LocalIpAddress = ipv4_address

        # Enable BGP MD5 Auth on NeighborRange
        if enable_md5:
            if not bgp_neighbor_range.Authentication == 'md5':
                self.IxNetwork.info('Setting BGP NeighborRange Authentication to \'md5\'.')
                bgp_neighbor_range.Authentication = 'md5'

            if not bgp_neighbor_range.Md5Key == md5_password:
                self.IxNetwork.info(f"Setting BGP NeighborRange MD5 password to \'{md5_password}\'")
                bgp_neighbor_range.Md5Key = md5_password
        else:
            if not bgp_neighbor_range.Authentication == 'null':
                self.IxNetwork.info('Setting BGP NeighborRange Authentication to null')
                bgp_neighbor_range.Authentication = 'null'

        if hold_timer:
            self.IxNetwork.info(f'Setting BGP NeighborRange Hold Timer to \'{hold_timer}\'.')
            bgp_neighbor_range.HoldTimer = hold_timer

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

    def start_ospf(self,
                   config: str,
                   config_local=True,
                   authentication_method=None,
                   md5_key=None,
                   md5_key_id=None,
                   hold_timer=None,
                   ipv4_address=None,
                   ipv4_mask_width=None,
                   ipv4_gateway=None):

        self.load_config(config, config_local)
        vport = self.connect_vport(vport_name='DUT Edge')

        # Adjust Interface IP
        ipv4_interface = vport.Interface.find().Ipv4.find()
        ipv4_interface.Gateway = ipv4_gateway
        ipv4_interface.Ip = ipv4_address
        ipv4_interface.MaskWidth = ipv4_mask_width

        # Adjust OSPF Protocol
        ospf = vport.Protocols.find().Ospf

        # Set OSPF Router
        ospf_router = ospf.Router.find()
        ospf_router.RouterId = ipv4_address

        # Set OSPF Interface
        ospf_router_interface = ospf_router.Interface.find()
        ospf_router_interface.InterfaceIpAddress = ipv4_address

        # Enable authentication if passed
        if authentication_method:
            self.IxNetwork.info(f'Setting OSPF Router Interface Authentication to: \'{authentication_method}\'')
            ospf_router_interface.AuthenticationMethods = authentication_method

        if md5_key:
            self.IxNetwork.info(f'Setting OSPF Router Interface Authentication Key to: \'{md5_key}\'')
            ospf_router_interface.Md5AuthenticationKey = str(md5_key)

        if md5_key_id:
            self.IxNetwork.info(f'Setting OSPF Router Interface Authentication Key Id to: \'{md5_key_id}\'')
            ospf_router_interface.Md5AuthenticationKeyId = str(md5_key_id)

        self.IxNetwork.info('Starting OSPF Protocol...')
        ospf.Start()
        self.IxNetwork.info('OSPF Protocol started.')

        self.IxNetwork.info('Checking for OSPF Full Nbrs to equal to 1...')
        ospf_aggregated_stats = self.SessionAssistant.StatViewAssistant(ViewName='OSPF Aggregated Statistics',
                                                                        Timeout=200)
        while True:
            try:
                while not ospf_aggregated_stats.CheckCondition(ColumnName='Full Nbrs.',
                                                               Comparator=StatViewAssistant.EQUAL,
                                                               ConditionValue=1,
                                                               Timeout=240):
                    self.IxNetwork.info('Waiting for OSPF Full Nbrs. to equal 1...')
                    time.sleep(10)
            except SyntaxError:
                continue
            except NotFoundError:
                print({'error': "OSPF Session Timeout"})
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