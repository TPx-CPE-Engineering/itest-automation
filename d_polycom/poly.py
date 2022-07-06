"""
poly.py

Author:
    - Cody Hill

Description:
    - Python file containing the class, functions and methods used by iTest
        for testing Poly VVX and CCX devices utilizing the Poly UC API.

    - Code was developed to be used with Poly UC Software 6.4.0 and above.
        Testing with any previous code versions is possible, but not supported.

    - Poly UC Software 6.4.0 API documentation:
        https://www.poly.com/content/dam/www/products/support/voice/vvx-business-ip-phones/other/ucsoftware-restapi-6-4-0-en.pdf
"""

import ipaddress
import json
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Disable urllib3 InsecureRequestWarnings
urllib3.disable_warnings(category=InsecureRequestWarning)

def validate_ip_address(ip_address: str):
    """Validates an IP address string

    Args:
        ip_address (str): IP address to validate

    Returns:
        True (bool): If the given string is a valid IP address
        Flase (bool): If the given string is not a valid IP address
    """

    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


class Poly:
    """Poly Class containing methods to interface with the Poly UC API.

    Params:
        - ip_address (str): IP address of the Poly object to create.
    """

    def __init__(self, ip_address: str):
        # Validate the Poly's IP address
        # If the the IP address is not valid, raise a ValueError Exception
        if not validate_ip_address(ip_address):
            raise ValueError('Unable to create Poly object!\nCheck the Poly\'s IP address.')

        # Set the self IP address
        self.ip_address = ip_address

        # HTTP header for Poly UC API
        self.HTTP_HEADER = {
            'Content-Type': 'application/JSON',
        }

        # Set the self phone number
        self.phone_number = self.get_line_one_phone_number()

        # Set the Poly's device information
        device_info = self.get_device_info()

        if device_info:
            self.model_number = device_info[1]['model_number']
            self.mac_address = device_info[1]['mac_address']
            self.firmware_version = device_info[1]['firmware_version']
        else:
            self.model_number = 'Unable to retrieve Device Info'
            self.mac_address = 'Unable to retrieve Device Info'
            self.firmware_version = 'Unable to retrieve Device Info'

        self.API_ERROR_CODES = {
            2000: 'API executed successfully.',
            4000: 'Invalid input parameters.',
            4001: 'Device busy.',
            4002: 'Line not registered.',
            4003: 'Operation not allowed.',
            4004: 'Operation Not Supported',
            4005: 'Line does not exist.',
            4006: 'URLs not configured.',
            4007: 'Call Does Not Exist',
            4008: 'Configuration Export Failed',
            4009: 'Input Size Limit Exceeded',
            4010: 'Default Password Not Allowed',
            4011: 'Contact not found',
            4400: 'Bad Request',
            4403: 'Forbidden',
            5000: 'Failed to process request.',
            5500: 'Internal Server Error'
        }


    def get_error_code_definition(self, error_code: int):
        """Provides the definition of the given API error code.

        Args:
            error_code (int): Error code to define.

        Returns:
            self.API_ERROR_CODES[error_code] (str): Definition of the given API error code.
        """

        return self.API_ERROR_CODES[error_code]


    def get_line_one_phone_number(self):
        """Gets the phone number registered on line one of the Poly.

        Returns:
            - line_one_phone_number (str): The phone number registered to line one
        """

        line_one_phone_number = self.line_info_v2()['data'][0]['Username']
        return line_one_phone_number


    def get_device_info(self):
        """Gets the Poly's device information.

        Returns:
            - False, device_info['Status'] (tuple): If unable to retrieve the
            device info, return the status of the API call

            - True, result (tuple): If the device info was successfully retrieved,
            return the model number, mac address, and firmware version of the Poly
        """

        device_info = self.device_info_v2()

        if device_info['Status'] != '2000':
            return False, device_info['Status']

        result = {
            'model_number': device_info['data']['ModelNumber'],
            'mac_address': device_info['data']['MACAddress'],
            'firmware_version': device_info['data']['Firmware']['Updater']
        }

        return True, result


    def api_post(self, path: str):
        """Sends an empty HTTP POST request to the Poly.

        Params:
            - path (str): HTTP POST request path.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        request = requests.post(f'https://Polycom:3724@{self.ip_address}{path}', headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def api_post_data(self, path: str, data: dict):
        """Sends an HTTP POST request to the Poly containing data.

        Params:
            - path (str): HTTP POST request path.
            - data (str): Data to send to the Poly UC API.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        request = requests.post(f'https://Polycom:3724@{self.ip_address}{path}', data=data, headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def api_get(self, path: str):
        """Sends an HTTP GET request to the Poly.

        Params:
            - path (str): HTTP GET request path.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        request = requests.get(f'https://Polycom:3724@{self.ip_address}{path}', headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def restart(self):
        """This API executes a safeRestart on phone. safeRestart ensures that all calls
        on the phone are ended before initiating phone restart.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_post('/api/v1/mgmt/safeRestart')
        return response


    def reboot(self):
        """This API executes a safeReboot on the phone. safeReboot ensures that all calls
        on the phone are ended before initiating phone reboot.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_post('/api/v1/mgmt/safeReboot')
        return response


    def factory_reset(self):
        """This API factory-resets the phone.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_post('/api/v1/mgmt/factoryReset')
        return response


    def network_info(self):
        """This API provides details about the phone’s network information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/network/info')
        print(type(response))
        return response


    def device_info(self):
        """This API provides details about the phone's information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/device/info')
        return response


    def device_info_v2(self):
        """This API provides general device information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v2/mgmt/device/info')
        return response


    def network_stats(self):
        """This API provides the phone’s network statistics information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/network/stats')
        return response


    def dial(self, dest: str, line: str = '1', _type: str = 'TEL'):
        """This API enables a user to initiate a call to a given number. Moreover, this API
        initiates the call and returns a response as an acknowledgment of request
        received.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Dest": "' + dest + '","Line": "' + line + '","Type": "' + _type + '"}}'

        response = self.api_post_data('/api/v1/callctrl/dial', data)

        if response['Status'] == '2000':
            return True, response

        return False, response


    def end_call(self, call_reference: str):
        """This API ends an active call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/endCall', data)

        if response['Status'] != '2000':
            return False

        return True, response


    def mute_call(self):
        """This API enables a user to mute the phone, if applicable.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"state": "1"}}'

        response = self.api_post_data('/api/v1/callctrl/mute', data)
        return response


    def unmute_call(self):
        """This API enables a user to un-mute the phone, if applicable.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"state": "0"}}'

        response = self.api_post_data('/api/v1/callctrl/mute', data)
        return response


    def transfer_call(self, call_reference: str, transfer_dest: str):
        """This API enables a user to transfer a call. In addition, this API always executes a
        blind transfer.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '", "TransferDest": "' + transfer_dest + '"}}'

        response = self.api_post_data('/api/v1/callctrl/transferCall', data)
        return response


    def send_dtmf(self, digits: str):
        """This API enables a user to send DTMF tones during an active call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"digits": "' + digits + '"}}'

        response = self.api_post_data('/api/v1/callctrl/sendDTMF', data)
        return response


    def call_logs(self, call_log_type: str = 'all'):
        """This API provides the phone’s call logs.

        Params:
            - call_log_type (str, optional): Type of call log to retrieve.
                - Options: [all/missed/received/placed]
                - Defaults to 'all'.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        if call_log_type == 'all':
            response = self.api_get('/api/v1/mgmt/callLogs')

        elif call_log_type == 'missed':
            response = self.api_get('/api/v1/mgmt/callLogs/missed')

        elif call_log_type == 'received':
            response = self.api_get('/api/v1/mgmt/callLogs/received')

        elif call_log_type == 'placed':
            response = self.api_get('/api/v1/mgmt/callLogs/placed')

        else:
            return False

        return response


    def sip_status(self):
        """This API provides the phone’s SIP level details for the user.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/webCallControl/sipStatus')
        return response


    def hold_call(self, call_reference: str):
        """This API allows the user to hold an active call.

        Params:
            - call_reference (str): CallHandle of current call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/holdCall', data)
        return response


    def resume_call(self, call_reference: str):
        """This API resumes the call which was previously on hold.

        Params:
            - call_reference (str): CallHandle of current call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/resumeCall', data)
        return response


    def answer_call(self, call_reference: str):
        """This API answers an incoming call.

        Params:
            - call_reference (str): CallHandle of current call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/answerCall', data)

        if response['Status'] != '2000':
            return False

        return True, response


    def ignore_call(self, call_reference: str):
        """This API allows the user to ignore an incoming call.

        Params:
            - call_reference (str): CallHandle of current call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/ignoreCall', data)
        return response


    def reject_call(self, call_reference: str):
        """This API allows the user to reject an incoming call.

        Params:
            - call_reference (str): CallHandle of current call.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/rejectCall', data)
        return response


    def poll_for_status(self):
        """This API polls the current state of the Poly.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/pollForStatus')
        return response


    def running_config(self):
        """This API provides information about running configuration on phone.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/device/runningConfig')
        return response


    def session_stats(self):
        """This API provides statistics of active media sessions on phone.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/media/sessionStats')
        return response

    def call_status(self):
        """This API provides all the information of calls on the phone.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/webCallControl/callStatus')
        return response

    def call_status_v2(self):
        """This API provides information about all the calls present on phone.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v2/webCallControl/callStatus')
        return response

    def line_info(self):
        """This API provides details about the phones's line information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v1/mgmt/lineInfo')
        return response

    def line_info_v2(self):
        """This API provides details about the phones's line information.

        Returns:
            - response (dict): Dictionary containing the response from the Poly UC API.
        """

        response = self.api_get('/api/v2/mgmt/lineInfo')
        return response

    def get_current_call_reference(self, line: int = 0):
        """Retrieves the CallHandle of the current active call.

        Params:
            - line (int, optional): Line number of which to retrieve the Call Reference of.
                - Defaults to 0.

        Returns:
            - False (bool): If unable to get the CallHandle of an active call on the given line.
            - True, call_reference (tuple)_type_: If the CallHandle was successfully retrieved
        """

        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        call_reference = call_status['data'][line]['CallHandle']
        return True, call_reference

    def is_ringing(self, line: int = 0):
        """Checks if the Poly's call status is currently 'Ringing'.

        Params:
            - line (int, optional): Line number of which to check is 'Ringing'. Defaults to 0.

        Returns:
            - False (bool): If there is no call data on the given line, or if the 'Ringing' status is 0.
            - True (bool): If the line's current 'Ringing' status is 1.
        """

        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        ringing_status = call_status['data'][line]['Ringing']

        if ringing_status == '0':
            return False

        if ringing_status == '1':
            return True

    def call_state(self, line: int = 0):
        """Gets the call state of the given line number.

        Params:
            - line (int, optional): Line number of which to get the current CallState. Defaults to 0.

        Returns:
            - False (bool): If there is no call data on the given line.
            - True, call_state (tuple): If the CallState was successfully retrieved.
        """

        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        call_state = call_status['data'][line]['CallState']

        return True, call_state

    def media_direction(self, line: int = 0):
        """Gets the media direction of the given line number.

        Params:
            - line (int, optional): Line number of which to get the current media direction. Defaults to 0.

        Returns:
            - False (bool): If there is no active call status data.
            - True, media_direction (tuple): If the media direction of the given line was successfully retrieved.
        """

        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        media_direction = call_status['data'][line]['Media Direction']

        return True, media_direction

    def get_device_uptime(self):
        """Retrieves the current device uptime.

        Returns:
            uptime (dict): Dictionary containing the device's current uptime statistics.
        """

        uptime = self.device_info_v2()['data']['UpTime']
        return uptime


if __name__ == '__main__':
    # print(__doc__)
    poly = Poly('192.168.0.90')
