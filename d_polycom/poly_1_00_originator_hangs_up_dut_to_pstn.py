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
from cpe_engineering.poly.poly_test_plan.iTest.poly import Poly

dut_poly = Poly('192.168.0.85')
pstn_poly = Poly('192.168.0.212')


def originate_call_from_dut_to_pstn(dut_poly: object, pstn_poly: object):
    """Originates call from the DUT Poly to the PSTN poly

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly (object): PSTN Poly object

    Returns:
        True (bool): If the call was successfully sent from the DUT Poly
        False (bool): If the call was unsuccessful from the DUT Poly
    """

    if not dut_poly.dial(pstn_poly.phone_number):
        return False

    time.sleep(5)
    return True


def verify_called_party_receives_ringing(pstn_poly: object):
    """Verifies that the PSTN Poly's Call State is 'Ringing'

    Args:
        pstn_poly (object): PSTN Poly object

    Returns:
        True (bool): If the PSTN Poly's Call State is 'Ringing'
        False (bool): If the PSTN Poly's Call State is not 'Ringing'
    """

    if not pstn_poly.is_ringing():
        return False

    return True


def verify_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the DUT Poly receives a Call State of 'RingBack'

    Args:
        dut_poly (object): DUT Poly object

    Returns:
        True (bool): If the PSTN Poly's Call State is 'RingBack'
        False (bool): If the PSTN Poly's Call State is not 'RingBack'
    """
     
    dut_call_state = dut_poly.call_state()

    if not dut_call_state:
        return False

    if dut_call_state[1] != 'RingBack':
        return False

    return True


def called_party_answers_call(pstn_poly):
    """Answers call from the PSTN Poly

    Args:
        pstn_poly (object): PSTN Poly object

    Returns:
        True (bool): If the call was successfully answered from the PSTN Poly
        False (bool): If the call was not successfully answered from the PSTN Poly
    """
    
    pstn_call_reference = pstn_poly.get_current_call_reference()

    if not pstn_call_reference:
        return False

    if not pstn_poly.answer_call(pstn_call_reference[1]):
        return False

    time.sleep(5)

    return True


def verify_two_way_call_path_is_established(dut_poly: object, pstn_poly: object):
    """Verifies that a 2-way call path is established

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly (object): PSTN Poly object

    Returns:
        True (bool): If a 2-way call path was successfully established
        False (bool): If a 2-way call path was not successfully established
    """
    
    dut_media_direction = dut_poly.media_direction()
    pstn_media_direction = pstn_poly.media_direction()

    if dut_media_direction[1] != 'sendrecv' or pstn_media_direction[1] != 'sendrecv':
        return False

    return True


def originating_party_hangs_up(dut_poly: object):
    """Hangs up the call from the DUT Poly

    Args: 
        dut_poly (object): DUT Poly object
    
    Returns: 
        True (bool): If the DUT Poly successfully ends the call
        False (bool): If the DUT Poly is unable to end the call
    """

    dut_call_reference = dut_poly.get_current_call_reference()

    if not dut_poly.end_call(dut_call_reference[1]):
        return False

    return True


def poly_1_00_originator_hangs_up_dut_to_pstn():
    """
    function poly_1_00_originator_hangs_up_dut_to_pstn(dut_poly, pstn_poly_1)

        - Originate a call from DUT Poly to PSTN Poly
            - Called party receives ringing
            - Originating party receives RingBack
            - Called party answers call and 2-way path is established

        - Originating party hangs up
            - Call is Released

    Returns:
        test_result (dict): Dictionary containing result of test
    """

    if not originate_call_from_dut_to_pstn(dut_poly, pstn_poly):
        return False, 'Unable to dial PSTN Poly from DUT Poly'

    if not verify_called_party_receives_ringing(pstn_poly):
        return False, 'PSTN Poly did not ring'
        
    if not verify_originating_party_receives_ringback(dut_poly):
        return False, 'DUT Poly did not receive RingBack'

    if not called_party_answers_call(pstn_poly): 
        return False, 'Unable to answer call from PSTN Poly'

    if not verify_two_way_call_path_is_established(dut_poly, pstn_poly):
        return False, 'Two way path connectivity was not established'

    if not originating_party_hangs_up(dut_poly):
        return False, 'Unable to end call from DUT Poly'

    return True


if __name__ == '__main__':
    print(poly_1_00_originator_hangs_up_dut_to_pstn())
