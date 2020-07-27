from BasePolycom import BasePolycom, POLYCOM_RETURN_CODES, VANILLA_PHONE
import json
import time

DUT_POLYCOM: BasePolycom
OFFICE_POLYCOM: BasePolycom


def create_polycom(ipv4_address, model_number, sip_address):
    global DUT_POLYCOM, OFFICE_POLYCOM
    DUT_POLYCOM = BasePolycom(ipv4_address=ipv4_address,
                              model_number=model_number,
                              sip_address=sip_address)

    OFFICE_POLYCOM = BasePolycom(ipv4_address='10.255.20.158',
                                 model_number='VVX 410',
                                 sip_address='7027265809')



def dial(phone_number_to_dial):
    response = DUT_POLYCOM.post_dial(dest=phone_number_to_dial)
    ref_data = json.loads(response.text)
    status = ref_data['Status']
    print({'status': POLYCOM_RETURN_CODES[status],
           'message': f'Dialed to {phone_number_to_dial} successfully'})


def get_call_status():
    response = DUT_POLYCOM.get_call_status()
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

    # Pre-Check
    res = DUT_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'PRE-CHECK: Status from DUT POLYCOM: {status}')

    res = OFFICE_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'PRE-CHECK: Status from OFFICE POLYCOM: {status}\n\n')
    # expecting 4007 error


    # 0. Call out (to OFFICE Phone)
    print(f'Step 0: Calling to {OFFICE_POLYCOM.sip_address} from DUT POLYCOM')
    res = DUT_POLYCOM.post_dial(dest=OFFICE_POLYCOM.sip_address)
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 0: Status from DUT POLYCOM: {status}\n\n')
    # expecting 2000 status

    time.sleep(5)


    # 1.Called party receives ringing
    res = OFFICE_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 1: Status from OFFICE POLYCOM: {status}')
    call_state = ref_data['data']['CallState']
    print(f'Step 1: Call State from OFFICE POLYCOM: {call_state}')
    call_handle = ref_data['data']['CallHandle']
    print(f'Step 1: Call Handle from OFFICE POLYCOM: {call_handle}\n\n')
    # expecting call status to be RingBack

    time.sleep(2)


    # 2. Originating party receives ring back
    res = DUT_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 2: Status from DUT POLYCOM: {status}')
    call_state = ref_data['data']['CallState']
    print(f'Step 2: Call State from DUT POLYCOM: {call_state}')
    call_handle2 = ref_data['data']['CallHandle']
    print(f'Step 2: Call Handle from DUT POLYCOM: {call_handle2}\n\n')
    # expecting call status to be RingBack

    time.sleep(2)


    # 3.Called party answers call and 2-way path is established"
    res = OFFICE_POLYCOM.post_answer_call()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 3: Status from OFFICE POLYCOM: {status}\n\n')

    time.sleep(2)

    # 3.2 Get call status from both
    # OFFICE POLYCOM
    res = OFFICE_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 1: Status from OFFICE POLYCOM: {status}')
    call_state = ref_data['data']['CallState']
    print(f'Step 1: Call State from OFFICE POLYCOM: {call_state}')
    call_handle = ref_data['data']['CallHandle']
    print(f'Step 1: Call Handle from OFFICE POLYCOM: {call_handle}\n\n')

    # DUT POLYCOM
    res = DUT_POLYCOM.get_call_status()
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 2: Status from DUT POLYCOM: {status}')
    call_state = ref_data['data']['CallState']
    print(f'Step 2: Call State from DUT POLYCOM: {call_state}')
    call_handle2 = ref_data['data']['CallHandle']
    print(f'Step 2: Call Handle from DUT POLYCOM: {call_handle2}\n\n')

    # 4. End call
    res = OFFICE_POLYCOM.post_end_call(call_handle=call_handle)
    ref_data = json.loads(res.text)
    status = ref_data['Status']
    print(f'Step 4: Status from OFFICE POLYCOM: {status}\n\n')
