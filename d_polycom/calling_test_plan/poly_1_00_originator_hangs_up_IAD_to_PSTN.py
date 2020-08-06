from BasePolycom import BasePolycom, POLYCOM_RETURN_CODES, DEFAULT_TESTER_POLYCOM
import json
import time

DUT_POLYCOM: BasePolycom
TESTER_POLYCOM: BasePolycom


def create_polycom(ipv4_address, model_number, sip_address):
    global DUT_POLYCOM, TESTER_POLYCOM
    DUT_POLYCOM = BasePolycom(ipv4_address=ipv4_address,
                              model_number=model_number,
                              sip_address=sip_address)

    TESTER_POLYCOM = BasePolycom(ipv4_address=DEFAULT_TESTER_POLYCOM['ipv4 address'],
                                 model_number=DEFAULT_TESTER_POLYCOM['model number'],
                                 sip_address=DEFAULT_TESTER_POLYCOM['sip address'])


if __name__ == '__main__':
    create_polycom(ipv4_address='10.255.20.157',
                   model_number='VVX 501',
                   sip_address='7027265813')

    DUT_POLYCOM.post_end_call(call_handle="0x3740b48")
    exit(1)
