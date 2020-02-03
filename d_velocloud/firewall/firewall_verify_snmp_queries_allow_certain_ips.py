#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge

"""
Test Case: Verify SNMP queries to the Edge, are allowed if SNMP Access 'Allow the following IPs' is checked and configured.
Expected Results: Configured IP's will be allowed to send SNMP queries while all others be denied.
Usage: Confirm SNMP Settings v2c is enabled. Configure Edge's Firewall SNMP Access to 'Allow the following IPs

Details:
Ensure SNMP Settings v2c is enabled. You can find that in Edge's Device tab, scroll down to SNMP Settings. Port set to
161, community set to "tpc1n0c", and Allowed IPs: "Any" checked. 

Test by setting Edge's Firewall SNMP Access to "Allow the following IPs" and enter an IP you can ssh into. 
"""

# TODO make sure description is correct