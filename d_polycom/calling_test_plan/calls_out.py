from BasePolycom import BasePolycom, POLYCOM_RETURN_CODES
import json
import time

POLYCOM: BasePolycom
POLYCOM2: BasePolycom


def create_polycom(ipv4_address, model_number, sip_address):
    global POLYCOM
    POLYCOM = BasePolycom(ipv4_address=ipv4_address,
                          model_number=model_number,
                          sip_address=sip_address)


def dial(phone_number_to_dial):
    response = POLYCOM.post_dial(dest=phone_number_to_dial)
    ref_data = json.loads(response.text)
    status = ref_data['Status']
    print({'status': POLYCOM_RETURN_CODES[status],
           'message': f'Dialed to {phone_number_to_dial} successfully'})


def get_call_status():
    response = POLYCOM.get_call_status()
    print(response)
    # ref_data = json.loads(response.text)
    # status = ref_data['Status']
    #
    # if status == '4007':
    #     print({'status': POLYCOM_RETURN_CODES[status]})
    #     exit(0)
    #
    # data = ref_data['data']
    # print(json.dumps(data))


if __name__ == '__main__':
    create_polycom(ipv4_address='10.255.20.157',
                   model_number='VVX 501',
                   sip_address='7027265813')

    # dial(phone_number_to_dial='7026284133')
    # time.sleep(5)
    get_call_status()
