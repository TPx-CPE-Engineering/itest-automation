"""
poly_1_02_terminator_hangs_up_dut_to_pstn.py

Author: Cody Hill

Scenario:
    - Originate a call from DUT Poly to PSTN Poly
        - Called party receives ringing
        - Originating party receives ring back
        - Called party answers call and 2-way path is established

    - Terminating party hangs up
        - Call is Released
"""

import time
import json


def originate_call_from_dut_to_pstn(dut_poly: object, pstn_poly_1: object):
    """Originates call from the DUT Poly to the PSTN poly

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object): PSTN Poly object
    """

    result = dut_poly.web_call_control_dial(pstn_poly_1.phone_number)

    time.sleep(5)

    print(json.dumps(result))


def verify_called_party_receives_ringing(pstn_poly_1: object):
    """Verifies that the PSTN Poly's Call State is 'Ringing'

    Args:
        pstn_poly_1 (object): PSTN Poly object
    """

    result = pstn_poly_1.get_ringing_status()

    print(json.dumps(result))


def verify_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the DUT Poly receives a Call State of 'RingBack'

    Args:
        dut_poly (object): DUT Poly object
    """

    result = dut_poly.check_for_ringback()

    print(json.dumps(result))


def called_party_answers_call(pstn_poly_1: object):
    """Answers call from the PSTN Poly

    Args:
        pstn_poly_1 (object): PSTN Poly object
    """
    
    pstn_call_reference = pstn_poly_1.get_current_call_reference()['call_reference']

    result = pstn_poly_1.web_call_control_answer_call(pstn_call_reference)

    time.sleep(5)

    print(json.dumps(result))


def verify_two_way_call_path_is_established(dut_poly: object, pstn_poly_1: object):
    """Verifies that a 2-way call path is established

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object): PSTN Poly object
    """
    
    dut_media_direction = dut_poly.get_media_direction()['media_direction']
    pstn_media_direction = pstn_poly_1.get_media_direction()['media_direction']

    if dut_media_direction != 'sendrecv':
        return {'dut_media_direction': dut_media_direction}
        
    if pstn_media_direction != 'sendrecv':
        return {'pstn_media_direction': pstn_media_direction}

    result = {
        'dut_media_direction': dut_media_direction,
        'pstn_media_direction': pstn_media_direction
    }

    print(json.dumps(result))


def terminating_party_hangs_up(pstn_poly_1: object):
    """Hangs up the call from the PSTN Poly

    Args: 
        dut_poly (object): DUT Poly object
    """

    dut_call_reference = pstn_poly_1.get_current_call_reference()['call_reference']

    result = pstn_poly_1.web_call_control_end_call(dut_call_reference)
    
    print(json.dumps(result))


if __name__ == '__main__':
    print(__doc__)
