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


def check_if_called_party_is_ringing(pstn_poly_1: object):
    """Verifies that the called party receives Ringing from the originating party

    Args:
        pstn_poly_1 (object): PSTN Poly 1 object
    """

    result = pstn_poly_1.get_ringing_status()

    print(json.dumps(result))


def check_if_originating_party_receives_ringback(dut_poly: object):
    """Verifies that the originating party received RingBack from the terminating party

    Args:
        dut_poly (object): DUT Poly object
    """

    result = dut_poly.check_for_ringback()

    print(json.dumps(result))


def release_call_from_dut(dut_poly: object):
    """Releases call from the DUT Poly

    Args:
        dut_poly (object): DUT Poly object
    """

    call_reference = dut_poly.get_current_call_reference()['call_reference']

    result = dut_poly.web_call_control_end_call(call_reference)

    print(json.dumps(result))


if __name__ == '__main__':
    print(__doc__)
