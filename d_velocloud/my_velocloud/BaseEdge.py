from my_velocloud import Globals
from velocloud.api_client import ApiClient
from velocloud.apis import AllApi
from velocloud.rest import ApiException
from velocloud.models import EdgeGetEdgeConfigurationStackResultItem, EdgeGetEdgeConfigurationStack, ConfigurationModule

from velocloud import configuration
from requests.packages import urllib3
urllib3.disable_warnings()
configuration.verify_ssl = False


class BaseEdge:
    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int, auto_operator_login=True, live_mode=False):

        self.client = ApiClient(host=Globals.VC_SERVER)
        self.api = AllApi(api_client=self.client)
        if auto_operator_login:
            try:
                self.client.authenticate(username=Globals.VC_USERNAME,
                                         password=Globals.VC_PASSWORD,
                                         operator=True)
            except ApiException as login_exception:
                print(login_exception)
                exit()

        self.id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port
        self.voice_segment_name = Globals.VOICE_SEGMENT_NAME
        self.configuration_stack = self.get_configuration_stack()
        self.edge_specific_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[0]
        self.enterprise_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[1]

        # Live Mode API
        if live_mode:
            from my_velocloud.LiveModeAPI import LiveModeAPI
            self.LiveMode = LiveModeAPI(api_client=self.client,
                                        edge_id=self.id,
                                        enterprise_id=self.enterprise_id)

    def refresh_configuration_stack(self):
        """
        Refreshes Configuration Stack for Edge
        """
        param = EdgeGetEdgeConfigurationStack(edgeId=self.id, enterpriseId=self.enterprise_id)
        self.configuration_stack = self.api.edgeGetEdgeConfigurationStack(param)
        self.edge_specific_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[0]
        self.enterprise_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[1]

    def get_configuration_stack(self):
        """
        Gets the Edge's Configuration Stack

        The Configuration Stack consists of the Edge Specific Profile and Enterprise Profile
        :return:
        """

        param = EdgeGetEdgeConfigurationStack(edgeId=self.id, enterpriseId=self.enterprise_id)
        return self.api.edgeGetEdgeConfigurationStack(param)

    def get_module_from_edge_specific_profile(self, module_name: str) -> ConfigurationModule:
        """
        Return a specific module from Edge's Edge Specific Profile

        Possible modules: 'controlPlane', 'deviceSettings', 'firewall', 'QOS', 'WAN'
        Enter the name of the module you want to get in module_name
        Returns empty ConfigurationModule class if module is not found
        """

        if not (module_name == 'controlPlane' or module_name == 'deviceSettings' or module_name == 'firewall' or
                module_name == 'QOS' or module_name == 'WAN'):
            print('Module name error. Module not one of the following:'
                  '\'controlPlane\', \'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'.'
                  'Your selection: {}'.format(module_name))

            return ConfigurationModule()

        for module in self.edge_specific_profile.modules:
            if module.name == module_name:
                return module

        return ConfigurationModule()

    def get_module_from_enterprise_profile(self, module_name: str) -> ConfigurationModule:
        """
        Return a specific module from Edge's Enterprise Profile

        Possible modules: 'controlPlane', 'deviceSettings', 'firewall', 'QOS', 'WAN'
        Enter the name of the module you want to get in module_name
        Returns empty ConfigurationModule class if module is not found
        """

        if not (module_name == 'controlPlane' or module_name == 'deviceSettings' or module_name == 'firewall' or
                module_name == 'QOS' or module_name == 'WAN'):
            print('Module name error. Module not one of the following:'
                  '\'controlPlane\', \'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'.'
                  'Your selection: {}'.format(module_name))

            return ConfigurationModule()

        for module in self.enterprise_profile.modules:
            if module.name == module_name:
                return module

        return ConfigurationModule()

    @staticmethod
    def get_segment_from_module(segment_name: str, module: ConfigurationModule) -> dict:
        """
        Gets the segment based on name from the given module

        Searches through the passed module for a segment who's name matches segment_name
        If no segment found, returns an empty dictionary
        """

        for seg in module.data['segments']:
            if seg['segment']['name'] == segment_name:
                return seg

        print('No segment named: \'{}\' found in module \'{}\'. Returning empty dict'.format(segment_name, module.name))
        return {}

    def get_wan_settings_links(self) -> [dict]:
        """
        Gets the Edge's WAN settings links in a list of dict

        Searching through the WAN module's data and collect the important information from
        the links

        WAN:
            data:
                networks: ...
                links:
                    RETURN ALL LINKS FOUND HERE
        """

        # Get WAN module
        wan_module = self.get_module_from_edge_specific_profile(module_name='WAN')

        # Return WAN links
        return wan_module.data['links']

    def get_cpe_ssh_port_forwarding_rule(self) -> dict:
        """
        Get Edge's CPE SSH port forwarding rule

        This rule holds information needed for other tests.
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Filter through the firewall and look for a port forwarding rule that has:
        # 1. 'port_forwarding' as its Type
        # 1. 'tcp' as its Protocol
        # 2. self.ssh_port as its WAN Port(s)
        # 3. '22' as its LAN Port

        tcp_proto = 6

        for inbound_rule in firewall_module.data['inbound']:
            if inbound_rule['action']['type'] == 'port_forwarding' and \
                    inbound_rule['match']['proto'] == tcp_proto and \
                    inbound_rule['match']['dport_low'] == self.ssh_port and \
                    inbound_rule['match']['dport_high'] == self.ssh_port and \
                    inbound_rule['action']['nat']['lan_port'] == 22:

                return inbound_rule

        # If no cpe ssh rule found return an empty dict
        print('Traceback: No CPE SSH Port Forwarding Rule found')
        return {}
