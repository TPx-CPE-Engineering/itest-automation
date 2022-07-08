"""
poly_1_01_call_cancel_dut_to_pstn.py

Author: Cody Hill

Scenario:
    - Originate a call from the DUT Poly to PSTN Poly 1 but call is 
    hung up before it is answered.

    1.) Called party receives ringing
    2.) Originating party receives ring back
    3.) Call is released from the DUT Poly
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


def check_if_called_party_is_ringing(pstn_poly_1: object):
    """Verifies that the called party receives Ringing from the originating party

    Args:
        pstn_poly_1 (object): PSTN Poly 1 object

    Returns:
        False (tuple): If the called party did not receive Ringing
        True (tuple): If the called party successfully received Ringing
    """

    result = pstn_poly_1.is_ringing()

    if not result:
        return False, result[1]

    return True, result[1]


def check_if_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the originating party received RingBack from the terminating party

    Args:
        dut_poly (object): DUT Poly object

    Returns:
        False (tuple): If the originating party did not receive RingBack
        True (tuple): If the originating party successfully receives RingBack
    """

    result = dut_poly.check_for_ringback()

    if not result:
        return False, result[1]

    return True, result[1]


def release_call_from_dut(dut_poly: object):
    """Releases call from the DUT Poly

    Args:
        dut_poly (object): DUT Poly object

    Returns:
        False (tuple): If the call was not released from the DUT Poly
        True (tuple): If the call was successfully released from the DUT Poly
    """

    call_reference = dut_poly.get_current_call_reference()

    if not call_reference():
        return False, call_reference[1]

    result = dut_poly.web_call_control_end_call(call_reference[1])

    if not result:
        return False, result[1]

    return True, result[1]


if __name__ == '__main__':
    print(__doc__)