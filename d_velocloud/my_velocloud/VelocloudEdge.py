from my_velocloud import Globals
from my_velocloud.VcoRequestManager import VcoRequestManager, ApiException
import json
import time
from bs4 import BeautifulSoup


class VeloCloudEdge(object):
    def __init__(self, edge_id, enterprise_id, cpe_ssh_port=None, authenticate=True, hostname=Globals.VC_SERVER,
                 verify_ssl=False, username=Globals.VC_USERNAME, password=Globals.VC_PASSWORD, is_operator=True):
        self.id = int(edge_id)
        self.enterprise_id = int(enterprise_id)
        self.cpe_ssh_port = cpe_ssh_port
        self.voice_segment_name = Globals.VOICE_SEGMENT_NAME
        self.client = VcoRequestManager(hostname=hostname, verify_ssl=verify_ssl)
        self.live_mode_token = None

        if authenticate:
            self.client.authenticate(username=username, password=password, is_operator=is_operator)

    def set_live_mode_token(self):
        """
        Set Live Mode Token

        Token is needed for Live Mode API Calls
        :return: None
        """

        method = '/liveMode/enterLiveMode'
        params = {'edgeId': self.id,
                  'enterpriseId': self.enterprise_id}

        response = self.client.call_api(method=method, params=params)
        self.live_mode_token = response['token']

    def get_edge_configuration_stack(self) -> list:
        """
        Get an edge's complete configuration profile, with all modules included
        :return: Edge's configuration stack as a list.
        """

        method = '/edge/getEdgeConfigurationStack/'
        params = {"edgeId": self.id,
                  "enterpriseId": self.enterprise_id}

        response = self.client.call_api(method=method, params=params)
        return response

    def get_edge_specific_profile(self) -> dict:
        """
        Get Edge's edge specific profile
        :return: Edge specific profile
        """

        edge_configuration_stack = self.get_edge_configuration_stack()
        # Index 0 contains edge specific profile
        return edge_configuration_stack[0]

    def get_enterprise_profile(self) -> dict:
        """
        Get Edge's enterprise profile
        :return: Edge's enterprise profile
        """

        edge_configuration_stack = self.get_edge_configuration_stack()
        # Index 1 contains edge specific profile
        return edge_configuration_stack[1]

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

    def get_device_settings_segments(self) -> list:
        """
        Get all Edge' device settings segments
        :return: All Edge's device settings segments
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        edges_segments = []

        for segment in device_settings['data']['segments']:
            edges_segments.append(segment)

        return edges_segments

    def get_a_device_settings_segment(self, segment_name) -> dict:
        """
        Get a specific Edge segment from device settings
        :param segment_name: Name of segment you want to get
        :return: Edge device settings segment
        """

        device_settings_segments = self.get_device_settings_segments()

        for segment in device_settings_segments:
            if segment['segment']['name'] == segment_name:
                return segment

        return {}

    def update_configuration_module(self, module):
        """
        Update Edge Configuration Module
        :param module: Module you wish to update
        :return: API response
        """

        update = {'data': module['data'],
                  'refs': module['refs'],
                  'description': None,
                  'name': module['name']}

        params = {'id': module['id'],
                  '_update': update,
                  'returnData': False,
                  'enterpriseId': self.enterprise_id}

        method = 'configuration/updateConfigurationModule'

        return self.client.call_api(method, params)

    def get_html_results_from_action_key(self, action_key):
        """
        Get HTML Results based on Live Mode action key
        :param action_key: Live Mode action key
        :return: None
        """

        method = "liveMode/readLiveData"
        params = {"token": self.live_mode_token}

        action = None
        status = None
        dump_complete = False

        # Continue to get live data until you obtain the data from the action key
        while not dump_complete:
            time.sleep(1)

            # We're looking for a status value greater than 1 as a cue that the remote procedure has
            # completed.
            #
            # Status enum is:
            #   0: PENDING
            #   1: NOTIFIED (i.e. Edge has acknowledge its receipt of the action)
            #   2: COMPLETE
            #   3: ERROR
            #   4: TIMED OUT

            live_data = self.client.call_api(method=method, params=params)

            # Check if Live Action is Active, after some time it becomes inactive
            # If so, get another Live Mode token
            try:
                is_live_mode_active = live_data.get("status", {}).get("isActive", None)
                if not is_live_mode_active:
                    # print('Live Mode is Not Active')
                    self.set_live_mode_token()
                    time.sleep(15)
                    continue
            except AttributeError:
                continue

            try:
                all_action_data = live_data.get("data", {}).get("liveAction", {}).get("data", [])
            except AttributeError:
                continue

            actions_matching_key = [a for a in all_action_data if a["data"]["actionId"] == action_key]
            if len(actions_matching_key) > 0:
                action = actions_matching_key[0]
                status = action["data"]["status"]
            else:
                status = 0

            dump_complete = status > 1

        if status == 2:
            diagnostics_results = action["data"].get("results", [])
            soup = BeautifulSoup(diagnostics_results[0]['results']['output'], "html.parser")
            return soup.get_text()
        else:
            raise ApiException(f"Encountered API error in call to '{method}'")

    def exit_live_mode(self):
        """
        Exit Live Mode gracefully
        :return: <str> Successful message: "Live Mode exited successfully"
        """

        method = 'liveMode/exitLiveMode'
        params = {'edgeId': self.id,
                  'enterpriseId': self.enterprise_id}

        exit_result = self.client.call_api(method=method, params=params)
        print(exit_result)

    @staticmethod
    def print_as_json(text):
        """
        Prints text as json

        To be used when trying to insert text into JSON beautifier
        :param text: Text to be printed in json format
        :return: None
        """

        print(json.dumps(text))


# Class for BGP Testing
class BGPVeloCloudEdge(VeloCloudEdge):
    
    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

        # Default Values for BGP Testing
        self.default_bgp_segment_name = 'Global Segment'
        self.default_bgp_segment = self.get_a_device_settings_segment(segment_name=self.default_bgp_segment_name)

    def enable_bgp_on_enterprise_segment(self, segment_name='Global Segment'):
        """
        Enable BGP on Enterprise's given segment
        :param segment_name: Segment name you want to enable BGP on
        :return: None
        """

        device_settings = self.get_module_from_enterprise_profile(module_name='deviceSettings')

        # Find the segment to enable BGP on
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Enable bgp
                segment['bgp']['enabled'] = True

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def disable_bgp_on_enterprise_segment(self, segment_name='Global Segment'):
        """
        Disable BGP on Enterprise's given segment
        :param segment_name: Segment name you want to enable BGP on
        :return: None
        """

        device_settings = self.get_module_from_enterprise_profile(module_name='deviceSettings')

        # Find the segment to disable BGP on
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Disable bgp
                segment['bgp']['enabled'] = False

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def overwrite_bgp_neighbors(self, neighbor_ip, neighbor_asn, segment_name='Global Segment'):
        """
        Overwrite a BGP Neighbor on Edge through Edge Override

        Old BGP Neighbors will be deleted
        :param segment_name: Name of Segment
        :param neighbor_ip: IP of BGP Neighbor to add
        :param neighbor_asn: ASN of BGP Neighbor to add
        :return: None
        """

        bgp_data = {
              "enabled": True,
              "routerId": None,
              "ASN": "65535",
              "networks": [],
              "neighbors": [
                {
                  "neighborIp": neighbor_ip,
                  "neighborAS": neighbor_asn,
                  "inboundFilter": {
                    "ids": []
                  },
                  "outboundFilter": {
                    "ids": []
                  }
                }
              ],
              "overlayPrefix": True,
              "disableASPathCarryOver": True,
              "uplinkCommunity": None,
              "connectedRoutes": True,
              "propagateUplink": False,
              "ospf": {
                "enabled": True,
                "metric": 20
              },
              "defaultRoute": {
                "enabled": False,
                "advertise": "CONDITIONAL"
              },
              "asn": None,
              "isEdge": True,
              "filters": [],
              "override": True
            }

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Update BGP on given segment
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                segment['bgp'] = bgp_data

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def get_vlan_ip_address_from_segment(self, segment_name='Global Segment') -> str:
        """
        Get VLAN IP Address from segment
        :param segment_name: Segment you want to retrieve VLAN IP Address from
        :return: IP Address
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        segment = self.get_a_device_settings_segment(segment_name=segment_name)
        segment_id = segment['segment']['segmentId']

        # Find VLAN
        for network in device_settings['data']['lan']['networks']:
            if network['segmentId'] == segment_id:
                return network['cidrIp']

    def get_new_bgp_neighbor_ip(self) -> str:
        """
        Get New BGP Neighbor IP taken from VLAN (that is on Global Segment) + 1
        :return:
        """
        from ipaddress import ip_address

        # Get VLAN IP
        ip = ip_address(address=self.get_vlan_ip_address_from_segment(segment_name='Global Segment'))
        # Increase VLAN IP address by 1 to set neighbor
        return str(ip + 1)

    def get_bgp_summary(self):
        """
        Show the existing BGP neighbor and received routes
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_SUM",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_neighbor_advertised_routes(self, segment_id, neighbor_ip):
        """
        Get the BGP routes advertised to a neighbor
        :param segment_id: Segment ID
        :param neighbor_ip: Neighbor IP
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_NBR_AD",
                            "parameters": [
                                f"{{\"segment\":\"{segment_id}\", \"nbr_ip\":\"{neighbor_ip}\"}}"
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_neighbor_received_routes(self, segment_id, neighbor_ip):
        """
        Get all the BGP routes learned from a neighbor before filters
        :param segment_id: Segment ID
        :param neighbor_ip: Neighbor IP
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_NBR_RCV",
                            "parameters": [
                                f"{{\"segment\":\"{segment_id}\", \"nbr_ip\":\"{neighbor_ip}\"}}"
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)