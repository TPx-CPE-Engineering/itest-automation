from my_velocloud import Globals
from my_velocloud.VcoRequestManager import VcoRequestManager, ApiException
import json
import time
from bs4 import BeautifulSoup


class VeloCloudEdge:
    def __init__(self, edge_id, enterprise_id, cpe_ssh_port=None, authenticate=True, hostname=Globals.VC_SERVER,
                 verify_ssl=False, username=Globals.VC_USERNAME, password=Globals.VC_PASSWORD, is_operator=True):
        self.id = edge_id
        self.enterprise_id = enterprise_id
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

    BGP_DEFAULT_SEGMENT_NAME = 'Global Segment'
    BGP_DEFAULT_SEGMENT_ID = 1

    def enable_bgp_on_enterprise_segment(self, segment_name=BGP_DEFAULT_SEGMENT_NAME):
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

        method = 'configuration/updateConfigurationModule'

        update = {'data': device_settings['data'],
                  'refs': device_settings['refs'],
                  'description': None,
                  'name': 'deviceSettings'}

        params = {'id': device_settings['id'],
                  '_update': update,
                  'returnData': False,
                  'enterpriseId': self.enterprise_id}

        response = self.client.call_api(method=method,
                                        params=params)
        print(response)

    def disable_bgp_on_enterprise_segment(self, segment_name=BGP_DEFAULT_SEGMENT_NAME):
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

        method = 'configuration/updateConfigurationModule'

        update = {'data': device_settings['data'],
                  'refs': device_settings['refs'],
                  'description': None,
                  'name': 'deviceSettings'}

        params = {'id': device_settings['id'],
                  '_update': update,
                  'returnData': False,
                  'enterpriseId': self.enterprise_id}

        response = self.client.call_api(method=method,
                                        params=params)
        print(response)

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
