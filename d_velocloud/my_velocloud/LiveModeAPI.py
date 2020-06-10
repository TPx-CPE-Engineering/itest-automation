from my_velocloud import Globals
from velocloud.rest import ApiException
import requests
import json
import re
import time
from bs4 import BeautifulSoup


class LiveModeAPI:
    def __init__(self, api_client, edge_id, enterprise_id):
        self.id = edge_id
        self.enterprise_id = enterprise_id

        self.api_client = api_client
        self._session = requests.Session()

        # To avoid creating a new cookie, reuse client's cookie for request Session
        cookie_obj = requests.cookies.create_cookie(name='velocloud.session',
                                                    domain=Globals.VC_SERVER,
                                                    value=api_client.default_headers['Cookie'][18:])
        self._session.cookies.set_cookie(cookie=cookie_obj)

        self._root_url = self._get_root_url(Globals.VC_SERVER)
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
        data = {"username": Globals.VC_USERNAME, "password": Globals.VC_PASSWORD}
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
        return {k: v for k, v in data.items() if v is not None}

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

    def get_html_results_from_action_key(self, action_key):
        """
        Get HTML Results based on Live Mode action key
        :param action_key: Live Mode action key
        :return:
        """

        method = "liveMode/readLiveData"
        params = {"token": self._token}

        live_data = None
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
            #   1: NOTIFIED (i.e. Edge has ack'ed its receipt of the action)
            #   2: COMPLETE
            #   3: ERROR
            #   4: TIMED OUT

            try:
                live_data = self.request(method=method, params=params, ignore_null_properties=True)
            except ApiException as e:
                print(f"Encountered LiveMode API error in call to {method}: {e}")
                exit(-1)

            # Check if Live Action is Active, after some time it becomes inactive
            # If so, get another Live Mode token
            try:
                is_live_mode_active = live_data.get("status", {}).get("isActive", None)
                if not is_live_mode_active:
                    # print('Live Mode is Not Active')
                    self._token = self._get_token()
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
            print(f"Encountered LiveMode API error in call to {method}")
            exit(-1)

    def exit_live_mode(self):
        """
        Exit Live Mode gracefully
        :return: <str> Successful message: "Live Mode exited successfully"
        """

        method = 'liveMode/exitLiveMode'
        params = {'edgeId': self.id,
                  'enterpriseId': self.enterprise_id}

        try:
            exit_result = self.request(method=method,
                                       params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        return "Live Mode exited successfully"

    def get_bgp_neighbor_advertised_routes(self, segment_id, neighbor_ip):
        """
        Get the BGP routes advertised to a neighbor
        :param segment_id: <int> Segment ID
        :param neighbor_ip: <str> Neighbor IP
        :return:
        """
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
                  "token": self._token
                }

        # Execute live action
        action_result = None
        try:
            action_result = self.request(method=method, params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_neighbor_received_routes(self, segment_id, neighbor_ip):
        """
        Get all the BGP routes learned from a neighbor before filters
        :param segment_id: <int> Segment ID
        :param neighbor_ip: <str> Neighbor IP
        :return:
        """
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
                  "token": self._token
                }

        # Execute live action
        action_result = None
        try:
            action_result = self.request(method=method, params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_summary(self):
        """
        Get the existing BGP neighbor and received routes
        :return:
        """
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
                  "token": self._token
                }

        # Execute live action
        action_result = None
        try:
            action_result = self.request(method=method, params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_ospf_database(self):
        """
        Get the OSPF link state database summary
        :return:
        """
        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_OSPF_DB",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self._token
                }

        # Execute live action
        action_result = None
        try:
            action_result = self.request(method=method, params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_ospf_neighbors(self):
        """
        Get all the OSPF neighbors and associated info
        :return:
        """
        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_OSPF_TBL",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self._token
                }

        # Execute live action
        action_result = None
        try:
            action_result = self.request(method=method, params=params)
        except ApiException as e:
            print(f"Encountered LiveMode API error in call to {method}: {e}")
            exit(-1)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)