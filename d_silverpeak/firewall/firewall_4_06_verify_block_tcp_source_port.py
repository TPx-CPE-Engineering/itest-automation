from my_silverpeak.base_edge import SPBaseEdge
import json
import time

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/23/2020

Test Case:      ZB Firewall - Block based on TCP source port
Expectations:   Configured traffic not allowed through firewall
Usage:          Configure outbound rule to deny all traffic based on TCP source port
                (Configuration > Templates > Default Template > Security Policies > Click on Zone (One to Default) in Matrix > Add Rule
                > Priority 1500 > Match Criteria "Port" Source:Destination > "Source 5060"
                Verify MSP traffic is blocked
                
                4/21/2020 Update - Source port changed from 443 to 5060
"""


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)


EDGE: SPEdge


def create_edge(edge_id: str, enterprise_id: str, ssh_port: str):
    """
    Creates Silver Peak Edge object
    :param edge_id: Silver Peak Edge ID
    :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
    :param ssh_port: SSH Port for CPE sitting behind Silver Peak Edge
    :return: None
    """
    global EDGE
    EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=ssh_port)


def add_firewall_rule_block_tcp_source_port():
    """
    Add firewall rule to block outbound TCP traffic based on source port 443 on map One to Default and priority 1500
    :return: None
    """

    # Set up firewall rule
    deny_source_port_5060_rule = {
                              "match": {
                                "acl": "",
                                "src_port": "5060"
                              },
                              "self": 1500,
                              "misc": {
                                "rule": "enable",
                                "logging": "disable",
                                "logging_priority": "0",
                                "tag": "iTest"
                              },
                              "comment": "iTest deny TCP traffic by source port 5060",
                              "gms_marked": False,
                              "set": {
                                "action": "deny"
                              }
                            }

    deny_source_port_5060_rule2 = {
                                  "self": "12_12",
                                  "prio": {
                                    "1500": {
                                      "match": {
                                        "acl": "",
                                        "src_port": "5060"
                                      },
                                      "self": 1500,
                                      "misc": {
                                        "rule": "enable",
                                        "logging": "disable",
                                        "logging_priority": "0",
                                        "tag": "iTest"
                                      },
                                      "comment": "iTest deny TCP traffic by source port 5060",
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

    # Get current firewall rules AKA security policies to Silverpeak
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add rule to security_policy_rules in map One to Default with priority 1500
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_source_port_5060_rule

    # Add to zones 'ONE to ONE' (12_12)
    security_policy_rules['map1']['12_12'] = deny_source_port_5060_rule2

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


def remove_firewall_rule_block_tcp_source_port():
    """
    Remove firewall rule to block outbound tcp traffic based on source port 443 on map One to Default and priority 1500
    :return: None
    """

    # Get Edge's Security Policy Rules data
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Delete firewall rule on "One to Default" map and a priority of 1500
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        # If KeyError then entry does not exists therefore you can say rule was successfully removed
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
        print({'error': None, 'rows': 1})
    else:
        print({'error': result.error, 'rows': 0})


if __name__ == '__main__':
    create_edge(edge_id='7.NE', enterprise_id='0', ssh_port="2201")
    # add_firewall_rule_block_tcp_source_port()
    remove_firewall_rule_block_tcp_source_port()