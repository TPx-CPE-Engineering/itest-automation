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
        True (bool): If the call was successfully sent from the DUT Poly
        False (tuple): If the call was unsuccessful from the DUT Poly
    """

    if not dut_poly.dial(pstn_poly_1.phone_number):
        return False, 'Unable to dial PSTN Poly from DUT Poly'

    time.sleep(5)
    return True


def verify_called_party_receives_ringing(pstn_poly_1: object):
    """Verifies that the PSTN Poly's Call State is 'Ringing'

    Args:
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (bool): If the PSTN Poly's Call State is 'Ringing'
        False (tuple): If the PSTN Poly's Call State is not 'Ringing'
    """

    if not pstn_poly_1.is_ringing():
        return False, 'PSTN Poly did not ring'

    return True


def verify_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the DUT Poly receives a Call State of 'RingBack'

    Args:
        dut_poly (object): DUT Poly object

    Returns:
        True (bool): If the PSTN Poly's Call State is 'RingBack'
        False (tuple): If the PSTN Poly's Call State is not 'RingBack'
    """
     
    if not dut_poly.check_for_ringback():
        return False, 'DUT Poly did not receive RingBack'

    return True


def called_party_answers_call(pstn_poly_1: object):
    """Answers call from the PSTN Poly

    Args:
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (bool): If the call was successfully answered from the PSTN Poly
        False (tuple): If the call was not successfully answered from the PSTN Poly
    """
    
    pstn_call_reference = pstn_poly_1.get_current_call_reference()

    if not pstn_call_reference:
        return False, 'Unable to get call reference from PSTN Poly'

    if not pstn_poly_1.answer_call(pstn_call_reference[1]):
        return False, 'Unable to answer call from PSTN Poly'

    time.sleep(5)

    return True


def verify_two_way_call_path_is_established(dut_poly: object, pstn_poly_1: object):
    """Verifies that a 2-way call path is established

    Args:
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object): PSTN Poly object

    Returns:
        True (bool): If a 2-way call path was successfully established
        False (tuple): If a 2-way call path was not successfully established
    """
    
    dut_media_direction = dut_poly.get_media_direction()
    pstn_media_direction = pstn_poly_1.get_media_direction()

    if dut_media_direction[1] != 'sendrecv' or pstn_media_direction[1] != 'sendrecv':
        return False, 'Two way path connectivity was not established'

    return True


def originating_party_hangs_up(dut_poly: object):
    """Hangs up the call from the DUT Poly

    Args: 
        dut_poly (object): DUT Poly object
    
    Returns: 
        True (bool): If the DUT Poly successfully ends the call
        False (tuple): If the DUT Poly is unable to end the call
    """

    dut_call_reference = dut_poly.get_current_call_reference()

    if not dut_poly.end_call(dut_call_reference[1]):
        return False, 'Unable to end call from DUT Poly'

    return True


def poly_1_00_originator_hangs_up_dut_to_pstn(dut_poly: object, pstn_poly_1: object):
    """Performs each test case scenario

        - Originate a call from DUT Poly to PSTN Poly
            - Called party receives ringing
            - Originating party receives RingBack
            - Called party answers call and 2-way path is established

        - Originating party hangs up
            - Call is Released

    Args: 
        dut_poly (object): DUT Poly object
        pstn_poly_1 (object) PSTN Poly object

    Returns:
        False (tuple): If any of the test case scenarios fail
        True (tuple): If all test case scenarios pass
    """

    if not originate_call_from_dut_to_pstn(dut_poly, pstn_poly_1):
        return False, 'Unable to dial PSTN Poly from DUT Poly'

    if not verify_called_party_receives_ringing(pstn_poly_1):
        return False, 'PSTN Poly did not ring'
        
    if not verify_originating_party_receives_ringback(dut_poly):
        return False, 'DUT Poly did not receive RingBack'

    if not called_party_answers_call(pstn_poly_1): 
        return False, 'Unable to answer call from PSTN Poly'

    if not verify_two_way_call_path_is_established(dut_poly, pstn_poly_1):
        return False, 'Two way path connectivity was not established'

    if not originating_party_hangs_up(dut_poly):
        return False, 'Unable to end call from DUT Poly'

    return True, 'Test poly_1_00_originator_hangs_up_dut_to_pstn passed'


if __name__ == '__main__':
    print(__doc__)
