import requests
import urllib3
import json
from urllib3.exceptions import InsecureRequestWarning

# Disable urllib3 InsecureRequestWarnings
urllib3.disable_warnings(category=InsecureRequestWarning)

class Poly:
    def __init__(self, ip_address: str):
        self.ip_address = ip_address

        # HTTP header for Poly UC API
        self.HTTP_HEADER = {
            'Content-Type': 'application/JSON',
        }

        self.phone_number = self.get_line_1_phone_number()

        device_info = self.get_device_info()

        if device_info:
            self.model_number = device_info[1]['model_number']
            self.mac_address = device_info[1]['mac_address']
            self.firmware_version = device_info[1]['firmware_version']
        else: 
            self.model_number = 'Unable to retrieve Device Info'
            self.mac_address = 'Unable to retrieve Device Info'
            self.firmware_version = 'Unable to retrieve Device Info'


    def get_line_1_phone_number(self):
        line_1_phone_number = self.line_info_v2()['data'][0]['Username']
        return line_1_phone_number

    
    def get_device_info(self):
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
        request = requests.post(f'https://Polycom:3724@{self.ip_address}{path}', headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def api_post_data(self, path: str, data: dict):
        request = requests.post(f'https://Polycom:3724@{self.ip_address}{path}', data=data, headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def api_get(self, path: str):
        request = requests.get(f'https://Polycom:3724@{self.ip_address}{path}', headers=self.HTTP_HEADER, verify=False)
        response = json.loads(request.text)
        return response


    def restart(self):
        response = self.api_post('/api/v1/mgmt/safeRestart')
        return response


    def reboot(self):
        response = self.api_post('/api/v1/mgmt/safeReboot')
        return response


    def factory_reset(self):
        response = self.api_post('/api/v1/mgmt/factoryReset')
        return response


    def network_info(self):
        response = self.api_get('/api/v1/mgmt/network/info')
        return response


    def device_info(self):
        response = self.api_get('/api/v1/mgmt/device/info')
        return response


    def device_info_v2(self):
        response = self.api_get('/api/v2/mgmt/device/info')
        return response


    def network_stats(self):
        response = self.api_get('/api/v1/mgmt/network/stats')
        return response


    def dial(self, dest: str, line: str = '1', _type: str = 'TEL'):
        data = '{"data": {"Dest": "' + dest + '","Line": "' + line + '","Type": "' + _type + '"}}'

        response = self.api_post_data('/api/v1/callctrl/dial', data)

        if response['Status'] == '2000':
            return True, response

        return False, response


    def end_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/endCall', data)

        if response['Status'] != '2000':
            return False

        return True, response


    def mute_call(self):
        data = '{"data": {"state": "1"}}'

        response = self.api_post_data('/api/v1/callctrl/mute', data)
        return response


    def unmute_call(self):
        data = '{"data": {"state": "0"}}'

        response = self.api_post_data('/api/v1/callctrl/mute', data)
        return response


    def transfer_call(self, call_reference: str, transfer_dest: str):
        data = '{"data": {"Ref": "' + call_reference + '", "TransferDest": "' + transfer_dest + '"}}'

        response = self.api_post_data('/api/v1/callctrl/transferCall', data)
        return response


    def send_dtmf(self, digits: str):
        data = '{"data": {"digits": "' + digits + '"}}'

        response = self.api_post_data('/api/v1/callctrl/sendDTMF', data)
        return response


    def call_logs(self, call_log_type: str = 'all'):
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


    def current_presence(self):
        response = self.api_get('/api/v1/mgmt/getPresence')
        return response


    def sip_status(self):
        response = self.api_get('/api/v1/webCallControl/sipStatus')
        return response


    def hold_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/holdCall', data)
        return response


    def resume_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/resumeCall', data)
        return response


    def answer_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/answerCall', data)

        if response['Status'] != '2000':
            return False

        return True, response


    def ignore_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/ignoreCall', data)
        return response


    def reject_call(self, call_reference: str):
        data = '{"data": {"Ref": "' + call_reference + '"}}'

        response = self.api_post_data('/api/v1/callctrl/rejectCall', data)
        return response


    def poll_for_status(self):
        response = self.api_get('/api/v1/mgmt/pollForStatus')
        return response


    def running_config(self):
        response = self.api_get('/api/v1/mgmt/device/runningConfig')
        return response


    def session_stats(self):
        response = self.api_get('/api/v1/mgmt/media/sessionStats')
        return response


    def call_status(self):
        response = self.api_get('/api/v1/webCallControl/callStatus')
        return response


    def call_status_v2(self):
        response = self.api_get('/api/v2/webCallControl/callStatus')
        return response


    def line_info(self):
        response = self.api_get('/api/v1/mgmt/lineInfo')
        return response


    def line_info_v2(self):
        response = self.api_get('/api/v2/mgmt/lineInfo')
        return response

    
    def get_current_call_reference(self, line: int = 0):
        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        call_reference = call_status['data'][line]['CallHandle']
        return True, call_reference


    def is_ringing(self, line: int = 0):
        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        ringing_status = call_status['data'][line]['Ringing']

        if ringing_status == '0':
            return False

        if ringing_status == '1':
            return True

    
    def call_state(self, line: int = 0):
        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        call_state = call_status['data'][line]['CallState']

        return True, call_state


    def media_direction(self, line: int = 0):
        call_status = self.call_status_v2()

        if not call_status['data']:
            return False

        media_direction = call_status['data'][line]['Media Direction']

        return True, media_direction

    
    def get_device_uptime(self):
        uptime = self.device_info_v2()['data']['UpTime']
        return uptime



if __name__ == '__main__':
    # print(__doc__)
    poly = Poly('192.168.0.212')

    print(poly.firmware_version)