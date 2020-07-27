import requests
import json
from collections import namedtuple

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

CREDS = 'Polycom:3724@'

POLYCOM_RETURN_CODES = {
    '2000': 'API executed successfully.',

    '4000': 'Invalid input parameters.',
    '4001': 'Device busy.',
    '4002': 'Line not registered.',
    '4003': 'Operation not allowed.',
    '4004': 'Operation Not Supported',
    '4005': 'Line does not exist.',
    '4006': 'URLs not configured.',
    '4007': 'Call Does Not Exist',
    '4008': 'Configuration Export Failed',
    '4009': 'Input Size Limit Exceeded',
    '4010': 'Default Password Not Allowed',

    '5000': 'Failed to process request.'
}

VANILLA_PHONE = {'ipv4 address': '10.255.20.158',
                 'model number': 'VVX 410',
                 'sip address': '7027265809',
                 }

Result = namedtuple('Result', [
    'status_code', 'status', 'data', 'url'
])


class BasePolycom:
    def __init__(self, ipv4_address: str, model_number: str, sip_address: str):
        self.ipv4_address: str = ipv4_address
        self.model_number: str = model_number
        self.sip_address: str = sip_address

        self.session: requests.Session = requests.Session()
        self.session.headers = {'Content-Type': 'application/json'}
        self.session.verify = False

    @staticmethod
    def parse_response(response: requests.models.Response):
        # return API call status, call handle (optional), and call state (optional) as dictionary

        ref_data = response.json()
        api_status_code = ref_data['Status']  # 2000 == success
        api_status = POLYCOM_RETURN_CODES[api_status_code]
        api_url = response.url

        try:
            data = ref_data['data']
        except KeyError:
            data = None

        return Result(status_code=api_status_code, status=api_status, data=data, url=api_url)

    def post_dial(self, dest, line='1', type='TEL'):
        """
        Initiate a call to a given number and returns a response as an acknowledgment of request received.
        :param dest: <str> Phone number dialing to
        :param line: <str> Line to be used, default is '1'
        :param type: <str> Type of call, default is 'TEL'
        :return: requests.models.Response
        """

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/dial'

        data = {"data": {
                        "Dest": dest,
                        "Line": line,
                        "Type": type
                        }
                }
        data = json.dumps(data)

        return self.parse_response(self.session.post(url=url, data=data))

    def get_call_status(self):
        """
        Provides all the information of calls on the phone.
        :return: response.models.Response
        """

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/webCallControl/callStatus'

        return self.parse_response(self.session.get(url=url))

    def post_answer_call(self):

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/answerCall'

        return self.parse_response(self.session.post(url=url))

    def post_end_call(self, call_handle):

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/endCall'

        data = {"data": {
                    "Ref": call_handle
                    }
                }

        data = json.dumps(data)

        return self.parse_response(self.session.post(url=url, data=data))