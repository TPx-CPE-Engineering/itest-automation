from my_velocloud import Globals
from my_velocloud.VcoRequestManager import VcoRequestManager, ApiException


class VeloCloudEdge:
    def __init__(self, edge_id, enterprise_id, cpe_ssh_port=None, authenticate=True, hostname=Globals.VC_SERVER,
                 verify_ssl=False, username=Globals.VC_USERNAME, password=Globals.VC_PASSWORD, is_operator=True):
        self.id = edge_id
        self.enterprise_id = enterprise_id
        self.cpe_ssh_port = cpe_ssh_port
        self.voice_segment_name = Globals.VOICE_SEGMENT_NAME
        self.client = VcoRequestManager(hostname=hostname, verify_ssl=verify_ssl)

        if authenticate:
            self.client.authenticate(username=username, password=password, is_operator=is_operator)

    def get_edge_configuration_stack(self) -> list:
        """
        Get an edge's complete configuration profile, with all modules included
        :return: Edge's configuration stack as a list.
        """

        method = '/edge/getEdgeConfigurationStack/'
        params = {"edgeId": self.id,
                  "enterpriseId": self.enterprise_id}

        try:
            response = self.client.call_api(method=method, params=params)
            return response
        except ApiException as e:
            print(e)

    def get_edge_specific_profile(self) -> dict:
        """
        Get Edge's edge specific profile
        :return: Edge specific profile
        """

        try:
            edge_configuration_stack = self.get_edge_configuration_stack()
            # Index 0 contains edge specific profile
            return edge_configuration_stack[0]
        except ApiException as e:
            print(e)

    def get_enterprise_profile(self) -> dict:
        """
        Get Edge's enterprise profile
        :return: Edge's enterprise profile
        """

        try:
            edge_configuration_stack = self.get_edge_configuration_stack()
            # Index 1 contains edge specific profile
            return edge_configuration_stack[1]
        except ApiException as e:
            print(e)

    def get_module_from_edge_specific_profile(self, module_name: str) -> dict:
        """
        Get a specific module from Edge's edge specific profile
        :param module_name: Module name that you want to retrieve
        :return: An edge specific module
        """

        if not (module_name == 'controlPlane' or
                module_name == 'deviceSettings' or
                module_name == 'firewall' or
                module_name == 'QOS' or
                module_name == 'WAN'):
            raise ApiException('Module name error. Module is not one of the following: \'controlPlane\', '
                               '\'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'. '
                               'Your selection: {}'.format(module_name))

        edge_specific_profile = self.get_edge_specific_profile()

        for module in edge_specific_profile['modules']:
            if module['name'] == module_name:
                return module

    def get_module_from_enterprise_profile(self, module_name: str) -> dict:
        """
        Get a specific module from Edge's enterprise profile
        :param module_name: Module name that you want to retrieve
        :return: An enterprise profile module
        """

        if not (module_name == 'controlPlane' or
                module_name == 'deviceSettings' or
                module_name == 'firewall' or
                module_name == 'QOS' or
                module_name == 'WAN'):
            raise ApiException('Module name error. Module is not one of the following: \'controlPlane\', '
                               '\'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'. '
                               'Your selection: {}'.format(module_name))

        enterprise_profile = self.get_enterprise_profile()

        for module in enterprise_profile['modules']:
            if module['name'] == module_name:
                return module
