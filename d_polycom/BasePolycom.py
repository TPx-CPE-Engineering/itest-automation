import requests
import json
from collections import namedtuple
from typing import Union

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

# 2nd Polycom Phone used along with DUT Polycom to perform testing
DEFAULT_TESTER_POLYCOM = {'ipv4 address': '10.255.20.180',
                          'model number': 'VVX 501',
                          'sip address': '7027265814',
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

        self.get_line_info()

    @staticmethod
    def parse_response(response: requests.models.Response, print_result=True, return_result=False) -> Result:
        ref_data = response.json()
        api_status_code = ref_data['Status']  # 2000 == success
        api_status = POLYCOM_RETURN_CODES[api_status_code]
        api_url = response.url

        try:
            api_data = ref_data['data']
        except KeyError:
            api_data = None

        result = {'status code': api_status_code,
                  'status': api_status,
                  'data': api_data,
                  'url': api_url}

        if print_result:
            print(json.dumps(result, sort_keys=True))

        if return_result:
            return Result(status_code=api_status_code, status=api_status, data=api_data, url=api_url)

    def post_dial(self, dest, line='1', type='TEL', print_result=True, return_result=False) -> Union[None, Result]:
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

        return self.parse_response(response=self.session.post(url=url,data=data),
                                   print_result=print_result,
                                   return_result=return_result)

    def get_call_status(self, print_result=True, return_result=False) -> Union[None, Result]:
        """
        Provides all the information of calls on the phone.
        :return: response.models.Response
        """

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/webCallControl/callStatus'

        return self.parse_response(self.session.get(url=url),
                                   print_result=print_result,
                                   return_result=return_result)

    def post_answer_call(self, print_result=True, return_result=False) -> Union[None, Result]:

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/answerCall'

        return self.parse_response(self.session.post(url=url),
                                   print_result=print_result,
                                   return_result=return_result)

    def post_end_call(self, call_handle, print_result=True, return_result=False) -> Union[None, Result]:

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/endCall'

        data = {"data": {
                    "Ref": call_handle
                    }
                }

        data = json.dumps(data)

        return self.parse_response(self.session.post(url=url, data=data),
                                   print_result=print_result,
                                   return_result=return_result)

    def get_session_stats(self, print_result=True, return_result=False) -> Union[None, Result]:

        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/mgmt/media/sessionStats'

        return self.parse_response(self.session.get(url=url),
                                   print_result=print_result,
                                   return_result=return_result)

    def get_voice_mos_scores(self, call_handle, print_result=True, return_result=False) -> Union[None, dict]:

        # Obtain the Session Stats for the phone
        response = self.get_session_stats(print_result=False, return_result=True)

        # Get calls data
        calls = response.data

        mos_scores = None
        # Filter through the calls based on the call handle aka Ref
        # There might be more than one call

        # Once the selected call is found, obtain the voice stream, other option is the video stream.
        # Return the voice stream based on the call handle aka Ref
        for call in calls:
            if call['Ref'] == call_handle:
                for stream in call['Streams']:
                    if stream['Category'] == '0:Voice':
                        mos_scores = {
                            'Ref': call_handle,
                            'TxMOSCQ': stream['TxMOSCQ'],
                            'TxMOSLQ': stream['TxMOSLQ'],
                            'RxMOSCQ': stream['RxMOSCQ'],
                            'RxMOSLQ': stream['RxMOSLQ']
                        }

        if mos_scores is None:
            mos_scores = {
                'Ref': f'Call hanldle: {call_handle} was not found',
                'TxMOSCQ': None,
                'TxMOSLQ': None,
                'RxMOSCQ': None,
                'RxMOSLQ': None
            }

        if print_result:
            print(json.dumps(mos_scores))

        if return_result:
            return mos_scores

    def validate_voice_mos_scores(self, call_handle, mos_score_threshold="3.6", print_result=True, return_result=False):

        voice_mos_scores = self.get_voice_mos_scores(call_handle=call_handle, print_result=False, return_result=True)

        voice_mos_scores_validation = {
            'All passed': False,
            'TxMOSCQ': {
                'passed': False,
                'score': '0'
            },
            'TxMOSLQ': {
                'passed': False,
                'score': '0'
            },
            'RxMOSCQ': {
                'passed': False,
                'score': '0'
            },
            'RxMOSLQ': {
                'passed': False,
                'score': '0'
            }
        }
        if float(voice_mos_scores['TxMOSCQ']) >= float(mos_score_threshold):
            voice_mos_scores_validation['TxMOSCQ']['passed'] = True
        voice_mos_scores_validation['TxMOSCQ']['score'] = voice_mos_scores['TxMOSCQ']

        if float(voice_mos_scores['TxMOSLQ']) >= float(mos_score_threshold):
            voice_mos_scores_validation['TxMOSLQ']['passed'] = True
        voice_mos_scores_validation['TxMOSLQ']['score'] = voice_mos_scores['TxMOSLQ']

        if float(voice_mos_scores['RxMOSCQ']) >= float(mos_score_threshold):
            voice_mos_scores_validation['RxMOSCQ']['passed'] = True
        voice_mos_scores_validation['RxMOSCQ']['score'] = voice_mos_scores['RxMOSCQ']

        if float(voice_mos_scores['RxMOSLQ']) >= float(mos_score_threshold):
            voice_mos_scores_validation['RxMOSLQ']['passed'] = True
        voice_mos_scores_validation['RxMOSLQ']['score'] = voice_mos_scores['RxMOSLQ']

        if voice_mos_scores_validation['TxMOSCQ']['passed'] and \
                voice_mos_scores_validation['TxMOSLQ']['passed'] and \
                voice_mos_scores_validation['RxMOSCQ']['passed'] and \
                voice_mos_scores_validation['RxMOSLQ']['passed']:
            voice_mos_scores_validation['All passed'] = True

        if print_result:
            print(json.dumps(voice_mos_scores_validation))

        if return_result:
            return voice_mos_scores_validation

    def end_any_active_call(self, print_result=True, return_result=False) -> Union[None, Result]:
        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/webCallControl/callStatus'
        response = self.parse_response(self.session.get(url=url), print_result=print_result, return_result=return_result)

        if not response.status_code == '4007':
            # Get call handle & End call
            call_handle = response.data['CallHandle']
            return self.post_end_call(call_handle=call_handle,
                                      print_result=print_result,
                                      return_result=return_result)

    def get_line_info(self, print_result=True, return_result=False):
        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/mgmt/lineinfo'

        return self.parse_response(self.session.get(url=url),
                                   print_result=print_result,
                                   return_result=return_result)

    def hold_call(self, print_result=True, return_result=False):
        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/holdCall'

        return self.parse_response(self.session.post(url=url),
                                   print_result=print_result,
                                   return_result=return_result)

    def resume_call(self, print_result=True, return_result=False):
        url = 'https://' + CREDS + self.ipv4_address + '/api/v1/callctrl/resumeCall'

        return self.parse_response(self.session.post(url=url),
                                   print_result=print_result,
                                   return_result=return_result)