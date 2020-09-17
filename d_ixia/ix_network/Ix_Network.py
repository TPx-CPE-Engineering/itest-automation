from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
from ixnetwork_restpy.errors import BadRequestError, NotFoundError
import time


# File Path where all IxNetwork configs live in
IX_NET_CONFIG_FILE_BASE = 'C:\\Users\\dataeng\\PycharmProjects\\iTest_Automation\\d_ixia\\ix_network\\configs\\'

# IP Address where IxNetwork Program (not chassis)
IX_NETWORK_IP = '10.255.20.7'

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
        except BadRequestError as e:
            print({'error': f"{e.message}"})
            exit(-1)
        self.IxNetwork.info('Config loaded.')

    def connect_vports(self, vports, force_ownership=True):
        # Connect every port in vports
        for port in vports:
            self.PortMap.Map(IpAddress=port['Chassis IP'],
                             CardId=port['Card'],
                             PortId=port['Port'],
                             Name=port['Name'])

        self.IxNetwork.info('Connecting to ports...')
        self.PortMap.Connect(ForceOwnership=force_ownership)
        self.IxNetwork.info('Ports connected.')

    def start_bgp_ix_network(self,
                             config: str,
                             vports: list,
                             vports_force_ownership=True,
                             config_local=True,
                             enable_md5=False,
                             md5_password=None,
                             hold_timer=None,
                             ipv4_address=None,
                             ipv4_mask_width=None,
                             ipv4_gateway=None):

        self.load_config(config, config_local)

        self.connect_vports(vports, )

        # Get Vport
        vport = self.IxNetwork.Vport.find()

        # Set IPv4 Interface
        interface = vport.Interface.find()
        print(interface)
        print('testing')
        # ipv4.add(Gateway=ipv4_gateway,
        #          Ip=ipv4_address,
        #          MaskWidth=ipv4_mask_width)

        # Enable BGP
        bgp = vport.Protocols.find().Bgp
        bgp.Enabled = True
        time.sleep(30)

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