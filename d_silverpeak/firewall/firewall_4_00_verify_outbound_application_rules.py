from my_silverpeak.base_edge import SPBaseEdge
import json
import time

"""
Silver Peak Test Plan v2
General EDGE Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/18/2020

Test Case:      ZB Firewall - Verify outbound application destination rules (NAT)
Expectations:   Configured traffic not allowed through firewall
Usage:          Configure outbound rule to deny traffic based on Application  (Configuration > Templates > Default Template > 
                Security Policies > Click on Zone (One to Default) in Matrix > Add Rule > Priority 1500 > 
                Match Criteria "Application" > "ICMP"
                Verify unable to register from CPE)
"""


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)


EDGE: SPEdge


# # TODO delete this function but before doing so check if test case works
# def set_globals(edge_id: str, enterprise_id: str):
#     """
#     Creates Silver Peak EDGE object
#     :param edge_id: Silver Peak EDGE ID
#     :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
#     :return: None
#     """
#     global EDGE
#     EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=0)
#
#     # Set REAL TIME overlay FW Zone to ONE
#     if not EDGE.is_fw_zone_set_for_overlay(fw_zone=EDGE.ONE_fw_zone, overlay=EDGE.RealTime_overlay):
#         EDGE.set_fw_zone_for_overlay(fw_zone=EDGE.ONE_fw_zone, overlay=EDGE.RealTime_overlay)
#
#     # SET LAN0 interface FW Zone to ONE
#     if not EDGE.is_fw_zone_set_for_interface(fw_zone=EDGE.ONE_fw_zone, interface=EDGE.LAN0_interface):
#         EDGE.set_fw_zone_for_interface(fw_zone=EDGE.ONE_fw_zone, interface=EDGE.LAN0_interface)


def create_edge(edge_id, enterprise_id):
    """
    Creates Silver Peak EDGE object
    :param edge_id: Silver Peak EDGE ID
    :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
    :return: None
    """
    global EDGE
    EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=0)

    # Set REAL TIME overlay FW Zone to ONE
    if not EDGE.is_fw_zone_set_for_overlay(fw_zone=EDGE.ONE_fw_zone, overlay=EDGE.RealTime_overlay):
        EDGE.set_fw_zone_for_overlay(fw_zone=EDGE.ONE_fw_zone, overlay=EDGE.RealTime_overlay)

    # SET LAN0 interface FW Zone to ONE
    if not EDGE.is_fw_zone_set_for_interface(fw_zone=EDGE.ONE_fw_zone, interface=EDGE.LAN0_interface):
        EDGE.set_fw_zone_for_interface(fw_zone=EDGE.ONE_fw_zone, interface=EDGE.LAN0_interface)


def add_icmp_block_outbound_app_rule():
    """
    Adds zone base firewall rule in zone One to Default with priority 1500 to block outbound application ICMP traffic
    :return: None
    """
    # Setup Deny Source Address rule
    deny_outbound_app_rule = {"match": {"acl": "",
                                          "application": 'Icmp'
                                          },
                                "self": 1500,
                                "misc": {"rule": "enable",
                                         "logging": "disable",
                                         "logging_priority": "0",
                                         "tag": "iTest"
                                         },
                                "comment": "iTest deny outbound application ICMP traffic",
                                "gms_marked": False,
                                "set": {"action": "deny"
                                        }
                                }
    
    deny_outbound_app_rule2 = {
                                  "self": "12_12",
                                  "prio": {
                                    "1500": {
                                      "match": {
                                        "acl": "",
                                        "application": 'Icmp'
                                      },
                                      "self": 1500,
                                      "misc": {
                                        "rule": "enable",
                                        "logging": "disable",
                                        "logging_priority": "0",
                                        "tag": "iTest"
                                      },
                                      "comment": "iTest deny outbound application ICMP traffic",
                                      "gms_marked": False,
                                      "set": {
                                        "action": "deny"
                                      }
                                    },
                                    "65535": {
                                      "match": {
                                        "acl": ""
                                      },
                                      "self": 65535,
                                      "misc": {
                                        "rule": "enable",
                                        "logging": "disable"
                                      },
                                      "comment": "",
                                      "gms_marked": False,
                                      "set": {
                                        "action": "deny"
                                      }
                                    }
                                  }
                                }

    # Get EDGE's Security Policy Rules data
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add new rule to Security Policy Rules
    # Add to 12_0 since that is 'One to Default'
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_outbound_app_rule

    # Add to zones 'ONE to ONE' (12_12)
    security_policy_rules['map1']['12_12'] = deny_outbound_app_rule2

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = EDGE.api.post_sec_policy(applianceID=EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        print({'error': None, 'rows': 1})
        time.sleep(10)
        EDGE.reset_port_flow(port=5060)
    else:
        print({'error': result.error, 'rows': 0})


def remove_icmp_block_outbound_app_rule():
    """
    Removes firewall rule in One to Default with priority 1500
    Firewall rule with priority 1500 is tied to ICMP application block rule
    :return: None
    """
    # Get EDGE's Security Policy Rules data
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Delete rule
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        # If KeyError, rule does not exist therefore removal was successful
        print({'error': None, 'rows': 0})
        return

    try:
        del security_policy_rules['map1']['12_12']
    except KeyError:
        # If KeyError then rule does not exist therefore removal successful
        print({'error': None, 'rows': 0})
        return

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = EDGE.api.post_sec_policy(applianceID=EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        d = {'error': None, 'rows': 1}
        print(d)
        time.sleep(10)
        EDGE.reset_port_flow(port=5060)
    else:
        d = {'error': result.error, 'rows': 0}
        print(d)


# # TODO delete this function but before doing so check if test case works
# def is_icmp_block_outbound_app_rule_present():
#     """
#     Prints yes or no (in json format) whether the firewall rule in One to Default with priority 1500 exists
#     Firewall rule with priority 1500 is tied to ICMP application block rule
#     :return: None
#     """
#     # Get EDGE's Security Policy Rules data
#     security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data
#
#     # Attempt to get Zone base Firewall rule with priority 1500 on One to Default zone
#     deny_source_address_rule = security_policy_rules.get('map1', None).get('12_0', None).get('prio', None)\
#         .get('1500', None)
#
#     # Checking rule...
#     if not deny_source_address_rule:
#         # If rule is None, then rule does not exists
#         print({"is_outbound_application_rule_present": 'no'})
#     else:
#         # If rule is not None, then rule exist
#         print({"is_outbound_application_rule_present": 'yes'})


if __name__ == '__main__':
    create_edge(edge_id='18.NE', enterprise_id='0')
