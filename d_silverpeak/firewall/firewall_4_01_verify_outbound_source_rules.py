from my_silverpeak.base_edge import SPBaseEdge
import json
import time

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/17/2020

Test Case:          ZB Firewall - Verify outbound IPaddr source rules (NAT)
Expectations:       Configured traffic not allowed through firewall
Usage:              Configure outbound rule to deny all traffic based on source address (Configuration > Templates > Default Template > Security Policies >
                    Click on Zone (One to Default) in Matrix > Add Rule > Priority 1500 > Match Criteria "Source IP" > "CPE IP Address"
                    Verify any traffic from CPE is dropped
"""


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)


DUT_EDGE: SPEdge


# def set_globals(edge_id: str, enterprise_id: str, ssh_port: str):
#     """
#     Creates Silver Peak Edge object
#     :param edge_id: Silver Peak Edge ID
#     :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
#     :param ssh_port: SSH Port for CPE sitting behind Silver Peak Edge
#     :return: None
#     """
#     global DUT_EDGE
#     DUT_EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=ssh_port)


def create_edge(edge_id, enterprise_id, ssh_port):
    """
    Creates Silver Peak Edge object
    :param edge_id: Silver Peak Edge ID
    :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
    :param ssh_port: SSH Port for CPE sitting behind Silver Peak Edge
    :return: None
    """
    global DUT_EDGE
    DUT_EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=ssh_port)


def add_deny_source_address_rule():
    """
    Add a firewall rule to block traffic from source ip: CPE IP on zone One to Default with priority 1500
    """
    # Get LAN IP of CPE behind Silverpeak and add subnet
    cpe_lan_ip = DUT_EDGE.get_cpe_lan_ip() + '/32'

    # Setup Deny Source Address rule
    deny_source_address_rule = {"match": {"acl": "",
                                          "src_ip": cpe_lan_ip
                                          },
                                "self": 1500,
                                "misc": {"rule": "enable",
                                         "logging": "disable",
                                         "logging_priority": "0",
                                         "tag": "iTest"
                                         },
                                "comment": "iTest deny outbound traffic from source IP {} (CPE LAN IP)".format(cpe_lan_ip),
                                "gms_marked": False,
                                "set": {"action": "deny"
                                        }
                                }

    deny_source_address_rule2 = {
                                  "self": "12_12",
                                  "prio": {
                                    "1500": {
                                      "match": {
                                        "acl": "",
                                        "src_ip": cpe_lan_ip
                                      },
                                      "self": 1500,
                                      "misc": {
                                        "rule": "enable",
                                        "logging": "disable",
                                        "logging_priority": "0",
                                        "tag": "iTest"
                                      },
                                      "comment": "iTest deny outbound traffic from source IP {} (CPE LAN IP)".format(cpe_lan_ip),
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

    # Get Edge's Security Policy Rules data
    security_policy_rules = DUT_EDGE.api.get_sec_policy(applianceID=DUT_EDGE.edge_id).data

    # Add new rule to Security Policy Rules
    # Add to zones 'ONE to DEFAULT' (12_0)
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_source_address_rule

    # Add to zones 'ONE to ONE' (12_12)
    security_policy_rules['map1']['12_12'] = deny_source_address_rule2

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = DUT_EDGE.api.post_sec_policy(applianceID=DUT_EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        print({'error': None, 'rows': 1})
        time.sleep(10)
        DUT_EDGE.reset_port_flow(port=5060)
    else:
        print({'error': result.error, 'rows': 0})


def remove_deny_source_address_rule():
    """
    Remove firewall rule to block traffic from source ip: CPE IP which is on zone One to Default with priority 1500
    :return:
    """
    # Get Edge's Security Policy Rules data
    security_policy_rules = DUT_EDGE.api.get_sec_policy(applianceID=DUT_EDGE.edge_id).data

    # Delete rule
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        # If KeyError then rule does not exist therefore removal successful
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
    result = DUT_EDGE.api.post_sec_policy(applianceID=DUT_EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        print({'error': None, 'rows': 1})
        time.sleep(10)
        DUT_EDGE.reset_port_flow(port=5060)
    else:
        print({'error': result.error, 'rows': 0})


# def is_deny_source_address_rule_present():
#     """
#     Prints yes or no (in json format) whether firewall rule to block traffic from source ip: CPE IP on zone One to Default with priority 1500 is present
#     :return:
#     """
#     # Get Edge's Security Policy Rules data
#     security_policy_rules = DUT_EDGE.api.get_sec_policy(applianceID=DUT_EDGE.edge_id).data
#
#     # Attempt to get rule on One to Default map with priority of 1500
#     deny_source_address_rule = security_policy_rules.get('map1', None).get('12_0', None).get('prio', None).get('1500', None)
#
#     if not deny_source_address_rule:
#         print({"is_deny_source_address_rule_present": 'no'})
#     else:
#         print({"is_deny_source_address_rule_present": 'yes'})


if __name__ == '__main__':
    create_edge(edge_id='18.NE', enterprise_id='0', ssh_port="2203")
    # add_deny_source_address_rule()
    # is_deny_source_address_rule_present()
    # remove_deny_source_address_rule()
