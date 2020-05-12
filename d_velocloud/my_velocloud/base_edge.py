from velocloud.api_client import ApiClient
from velocloud.apis import AllApi
from velocloud.rest import ApiException
from velocloud.models import EdgeGetEdgeConfigurationStackResultItem, EdgeGetEdgeConfigurationStack, ConfigurationModule

import requests
import json
import re


from velocloud import configuration
from requests.packages import urllib3
urllib3.disable_warnings()
configuration.verify_ssl = False

VC_SERVER = 'cpevc.lab-sv.telepacific.com'
VC_USERNAME = 'juan.brena@tpx.com'
VC_PASSWORD = '1Maule1!'


class BaseEdge:
    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int, auto_operator_login=True, live_mode=False):

        self.client = ApiClient(host=VC_SERVER)
        self.api = AllApi(api_client=self.client)
        if auto_operator_login:
            try:
                self.client.authenticate(username=VC_USERNAME,
                                         password=VC_PASSWORD,
                                         operator=True)
            except ApiException as login_exception:
                print(login_exception)
                exit()

        self.id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port
        self.voice_segment_name = 'Voice'
        self.configuration_stack = self.get_configuration_stack()
        self.edge_specific_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[0]
        self.enterprise_profile: EdgeGetEdgeConfigurationStackResultItem = self.configuration_stack[1]

        # Live Mode API
        if live_mode:
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

        print('No segment named: {} found in module {}'.format(segment_name, module.name))
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


class LiveModeAPI:
    def __init__(self, api_client, edge_id, enterprise_id):
        self.id = edge_id
        self.enterprise_id = enterprise_id

        self.api_client = api_client
        self._session = requests.Session()

        # To avoid creating a new cookie, reuse client's cookie for request Session
        cookie_obj = requests.cookies.create_cookie(name='velocloud.session',
                                                    domain=VC_SERVER,
                                                    value=api_client.default_headers['Cookie'][18:])
        self._session.cookies.set_cookie(cookie=cookie_obj)

        self._root_url = self._get_root_url(VC_SERVER)
        self._portal_url = self._root_url + "/portal/"
        self._live_pull_url = self._root_url + "/livepull/liveData/"
        self._verify_ssl = False
        self._seqno = 0
        self._token = self._get_token()

    def authenticate(self, is_operator=True):
        """
        Authenticate to API - on success, a cookie is stored in the session
        """
        path = "/login/operatorLogin" if is_operator else "/login/enterpriseLogin"
        url = self._root_url + path
        data = {"username": VC_USERNAME, "password": VC_PASSWORD}
        headers = {"Content-Type": "application/json"}
        r = self._session.post(url, headers=headers, data=json.dumps(data),
                               allow_redirects=False, verify=self._verify_ssl)

    def request(self, method, params, ignore_null_properties=False):
        """
        Build and submit a request
        Returns method result as a Python dictionary
        """
        self._seqno += 1

        headers = {"Content-Type": "application/json"}
        method = self._clean_method_name(method)
        payload = {"jsonrpc": "2.0",
                   "id": self._seqno,
                   "method": method,
                   "params": params}

        if method == "liveMode/readLiveData" or method == "liveMode/requestLiveActions":
            url = self._live_pull_url
        else:
            url = self._portal_url

        r = self._session.post(url, headers=headers,
                               data=json.dumps(payload), verify=self._verify_ssl)

        kwargs = {}
        if ignore_null_properties:
            kwargs["object_hook"] = self._remove_null_properties
        response_dict = r.json(**kwargs)
        if "error" in response_dict:
            raise ApiException(response_dict["error"]["message"])
        return response_dict["result"]

    @staticmethod
    def _remove_null_properties(data):
        return {k: v for k, v in data.iteritems() if v is not None}

    @staticmethod
    def _clean_method_name(raw_name):
        """
        Ensure method name is properly formatted prior to initiating request
        """
        return raw_name.strip("/")

    @staticmethod
    def _get_root_url(hostname):
        """
        Translate VCO hostname to a root url for API calls
        """
        if hostname.startswith("http"):
            re.sub("http(s)?://", "", hostname)
        proto = "https://"
        return proto + hostname

    def _get_token(self):
        """
        Get Live Mode Token needed to do LiveMode Requests
        :return: str Token
        """

        response = self.request(method="liveMode/enterLiveMode", params={'enterpriseId': self.enterprise_id,
                                                                         'id': self.id})

        return response['token']

