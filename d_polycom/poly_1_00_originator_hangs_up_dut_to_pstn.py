"""
poly_1_00_originator_hangs_up_dut_to_pstn.py

Author: Cody Hill

Scenario:
    - Originate a call from DUT Poly to PSTN Poly
        - Called party receives ringing
        - Originating party receives ring back
        - Called party answers call and 2-way path is established

    - Originating party hangs up
        - Call is Released
"""

import time


def originate_call_from_dut_to_pstn(dut_poly: object, pstn_poly_1: object):
    """Originates call from the DUT Poly to the PSTN poly

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (tuple): If the call was successfully sent from the DUT Poly
        False (tuple): If the call was unsuccessful from the DUT Poly
    """

    result = dut_poly.web_call_control_dial(pstn_poly_1.phone_number)

    if not result:
        return False, result[1]

    time.sleep(5)
    return True, result[1]


def verify_called_party_receives_ringing(pstn_poly_1: object):
    """Verifies that the PSTN Poly's Call State is 'Ringing'

    Args:
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (tuple): If the PSTN Poly's Call State is 'Ringing'
        False (tuple): If the PSTN Poly's Call State is not 'Ringing'
    """

    result = pstn_poly_1.is_ringing()

    if not result:
        return False, {'Status': 'Called party did not receive ringing'}

    return True


def verify_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the DUT Poly receives a Call State of 'RingBack'

    Args:
        dut_poly (object): DUT Poly object

    Returns:
        True (bool): If the PSTN Poly's Call State is 'RingBack'
        False (tuple): If the PSTN Poly's Call State is not 'RingBack'
    """

    result = dut_poly.check_for_ringback()
     
    if not result:
        return False, result[1]

    return True, result[1]


def called_party_answers_call(pstn_poly_1: object):
    """Answers call from the PSTN Poly

    Args:
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (tuple): If the call was successfully answered from the PSTN Poly
        False (tuple): If the call was not successfully answered from the PSTN Poly
    """
    
    pstn_call_reference = pstn_poly_1.get_current_call_reference()

    if not pstn_call_reference:
        return False, pstn_call_reference

    result = pstn_poly_1.web_call_control_answer_call(pstn_call_reference[1])

    if not result:
        return False, result[1]

    time.sleep(5)

    return True, result[1]


def verify_two_way_call_path_is_established(dut_poly: object, pstn_poly_1: object):
    """Verifies that a 2-way call path is established

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (tuple): If a 2-way call path was successfully established
        False (tuple): If a 2-way call path was not successfully established
    """
    
    dut_media_direction = dut_poly.get_media_direction()
    pstn_media_direction = pstn_poly_1.get_media_direction()

    if dut_media_direction[1] != 'sendrecv':
        return False, {
            'dut_media_direction': dut_media_direction[1]
        }
        
    if pstn_media_direction[1] != 'sendrecv':
        return False, {
            'pstn_media_direction': pstn_media_direction[1]
        }

    result = {
        'dut_media_direction': dut_media_direction[1],
        'pstn_media_direction': pstn_media_direction[1]
    }

    return True, result


def originating_party_hangs_up(dut_poly: object):
    """Hangs up the call from the DUT Poly

    Args: 
        dut_poly (object): DUT Poly object
    
    Returns: 
        True (tuple): If the DUT Poly successfully ends the call
        False (tuple): If the DUT Poly is unable to end the call
    """

    dut_call_reference = dut_poly.get_current_call_reference()

    result = dut_poly.web_call_control_end_call(dut_call_reference[1])

    if not result:
        return False, result[1]

    return True, result[1]


if __name__ == '__main__':
    print(__doc__)
