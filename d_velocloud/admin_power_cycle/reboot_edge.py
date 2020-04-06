import time
from datetime import datetime
import requests
import json
import re
import urllib3
urllib3.disable_warnings()


class ApiException(Exception):
    pass


class VcoRequestManager(object):

    def __init__(self, hostname, verify_ssl=True):
        self._session = requests.Session()
        self._verify_ssl = verify_ssl
        self._root_url = self._get_root_url(hostname)
        self._portal_url = self._root_url + "/portal/"
        self._livepull_url = self._root_url + "/livepull/liveData/"
        self._seqno = 0

    def _get_root_url(self, hostname):
        """
        Translate VCO hostname to a root url for API calls
        """
        if hostname.startswith("http"):
            re.sub('http(s)?://', '', hostname)
        proto = "https://"
        return proto + hostname

    def authenticate(self, username, password, is_operator=True):
        """
        Authenticate to API - on success, a cookie is stored in the session
        """
        path = "/login/operatorLogin" if is_operator else "/login/enterpriseLogin"
        url = self._root_url + path
        data = { "username": username, "password": password }
        headers = { "Content-Type": "application/json" }
        r = self._session.post(url, headers=headers, data=json.dumps(data),
                               allow_redirects=False, verify=self._verify_ssl)

    def call_api(self, method, params):
        """
        Build and submit a request
        Returns method result as a Python dictionary
        """
        self._seqno += 1
        headers = { "Content-Type": "application/json" }
        method = self._clean_method_name(method)
        payload = { "jsonrpc": "2.0",
                    "id": self._seqno,
                    "method": method,
                    "params": params }

        if method in ("liveMode/readLiveData", "liveMode/requestLiveActions", "liveMode/clientExitLiveMode"):
            url = self._livepull_url
        else:
            url = self._portal_url

        r = self._session.post(url, headers=headers,
                               data=json.dumps(payload), verify=self._verify_ssl)

        response_dict = r.json()
        if "error" in response_dict:
            raise ApiException(response_dict["error"]["message"])
        return response_dict["result"]

    def _clean_method_name(self, raw_name):
        """
        Ensure method name is properly formatted prior to initiating request
        """
        return raw_name.strip("/")


class RebootEdge:

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        self.edge_id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port

        client = VcoRequestManager(hostname='cpevc.lab-sv.telepacific.com', verify_ssl=False)
        client.authenticate(username='juan.brena@tpx.com', password='1Maule1!', is_operator=True)
        self.client = client

    def get_live_mode_token(self) -> str:
        """
        Get Live Mode Token needed to do LiveMode Requests
        :return: str Token
        """
        response = EDGE.client.call_api(method="liveMode/enterLiveMode", params={'enterpriseId': self.enterprise_id, 'id': self.edge_id})
        return response['token']

    def live_action_reboot(self):
        """
        Reboot Edge through live mode actions
        :return: None
        """
        live_mode_token = self.get_live_mode_token()
        try:
            response = self.client.call_api(method='liveMode/requestLiveActions', params={'token': live_mode_token,
                                                                                          'actions': [
                                                                                              {'action': 'reboot',
                                                                                               'parameters': {}
                                                                                               }
                                                                                            ]})
            print({'error': None, 'rows': 1})
        except ApiException as e:
            print({'error': e, 'rows': 0})

    def get_events(self, interval_start=None):
        """
        Get Edge's events with optional interval start
        :param: Events Interval start in unix time
        :return: list, Edges Events
        """

        # Set param for events api call
        if interval_start:
            params = {'edgeId': self.edge_id, 'enterpriseId': self.enterprise_id, 'interval': {'start': EPOCH}}
        else:
            params = {'edgeId': self.edge_id, 'enterpriseId': self.enterprise_id}

        # Return Edge's Events
        return self.client.call_api(method='/event/getEnterpriseEvents', params=params)['data']


EDGE: RebootEdge
# Used to get events from this epoch
EPOCH = int()


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = RebootEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def reboot_edge():
    global EPOCH
    EPOCH = int(round(time.time() * 1000))
    EDGE.live_action_reboot()


def find_shut_and_start_event_time_difference():
    """
    Find the time difference between the Edges 'Shutting down' event and 'Online' event
    :return: Prints time difference
    """
    events = EDGE.get_events(interval_start=EPOCH)

    # Look for 'shutting down' and 'online' event and return time between
    has_shutting_down_event = {'result': False, 'event time': None}
    has_online_event = {'result': False, 'event time': None}

    for event in reversed(events):
        if event['event'] == 'MGD_EXITING' and event['message'] == 'Management Daemon Exiting on signal 0':
            has_shutting_down_event['result'] = True
            utc_dt = datetime.strptime(event['eventTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            has_shutting_down_event['event time'] = (utc_dt - datetime(1970, 1, 1)).total_seconds()
            break

    while True:
        events = EDGE.get_events(interval_start=EPOCH)

        for event in reversed(events):
            if event['event'] == 'MGD_START' and 'Management Daemon Started' in event['message']:
                has_online_event['result'] = True
                utc_dt = datetime.strptime(event['eventTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                has_online_event['event time'] = (utc_dt - datetime(1970, 1, 1)).total_seconds()
                break

        if has_online_event['result']:
            break
        else:
            time.sleep(10)

    # If both events are found, print out the time it took between events
    if has_shutting_down_event['result'] and has_online_event['result']:
        converted_online = datetime.fromtimestamp(has_online_event['event time'])
        converted_shut = datetime.fromtimestamp(has_shutting_down_event['event time'])
        total_seconds = (converted_online - converted_shut).total_seconds()
        minutes = int(total_seconds / 60)
        seconds = total_seconds % 60
        print("Time between Edge 'Shutting down' and 'Online' events: {} minutes {} seconds, ({}s)".format(minutes, seconds, total_seconds))

    else:
        if not has_shutting_down_event['result']:
            print({'error': "'Shut Down' Event not found"})
        if not has_online_event['result']:
            print({'error': "'Online' Event not found"})


def find_shut_and_edge_interface_up_event_time_difference():
    """
    Find the time difference between the Edges 'Shutting down' event and 'Edge up' event
    :return: Prints time difference
    """
    events = EDGE.get_events(interval_start=EPOCH)

    # Look for 'shutting down' and 'edge interface up' event and return time between
    has_shutting_down_event = {'result': False, 'event time': None}
    has_edge_interface_up_event = {'result': False, 'event time': None, 'message': None}

    for event in reversed(events):
        if event['event'] == 'MGD_EXITING' and event['message'] == 'Management Daemon Exiting on signal 0':
            has_shutting_down_event['result'] = True
            utc_dt = datetime.strptime(event['eventTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            has_shutting_down_event['event time'] = (utc_dt - datetime(1970, 1, 1)).total_seconds()
            break

    while True:
        events = EDGE.get_events(interval_start=EPOCH)

        for event in reversed(events):
            if event['event'] == 'EDGE_INTERFACE_UP':
                has_edge_interface_up_event['result'] = True
                utc_dt = datetime.strptime(event['eventTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                has_edge_interface_up_event['event time'] = (utc_dt - datetime(1970, 1, 1)).total_seconds()
                break

        if has_edge_interface_up_event['result']:
            break
        else:
            time.sleep(10)

    if has_shutting_down_event['result'] and has_edge_interface_up_event['result']:
        converted_online = datetime.fromtimestamp(has_edge_interface_up_event['event time'])
        converted_shut = datetime.fromtimestamp(has_shutting_down_event['event time'])
        total_seconds = (converted_online - converted_shut).total_seconds()
        minutes = int(total_seconds / 60)
        seconds = total_seconds % 60
        print("Time between Edge 'Shutting down' and 'Edge Interface Up' events: {} minutes {} seconds, ({}s)".format(minutes, seconds, total_seconds))


def print_all_edge_reboot_events():
    """
    Prints all edge events, as a list, starting from when the reboot started
    :return: None
    """

    events = EDGE.get_events(interval_start=EPOCH)

    events_list = []

    for event in reversed(events):
        events_list.append(event['message'])

    print(events_list)


if __name__ == '__main__':
    create_edge(edge_id=1, enterprise_id=1, ssh_port=2201)
    reboot_edge()
    time.sleep(120)
    find_shut_and_start_event_time_difference()
    find_shut_and_edge_interface_up_event_time_difference()
