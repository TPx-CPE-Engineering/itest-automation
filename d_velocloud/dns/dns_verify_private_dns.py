#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from .dns_base_edge import *


"""
Test Case: Verify private DNS from CPE behind VCE
Expected Results: Verify CPE replies to a snmpwalk request when 1:1 NAT rule is enabled on the SD-WAN
Usage: Enable 1:1 NAT rule for CPE on SD-WAN, execute a snmpwalk request to the SD-WAN's public WAN IP, and verify CPE replies.
"""