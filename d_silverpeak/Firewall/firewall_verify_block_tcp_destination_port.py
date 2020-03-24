from my_silverpeak.base_edge import SPBaseEdge
import json

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/23/2020

Test Case:      ZB Firewall - Block based on TCP destination port
Expectations:   Configured traffic not allowed through firewall
Usage:          Configure outbound rule to deny all traffic based on TCP destination port
                (Configuration > Templates > Default Template > Security Policies > Click on Zone (One to Default) in Matrix > Add Rule
                > Priority 1500 > Match Criteria "Port" Source:Destination > "Destination 443"
                Verify MSP traffic is blocked
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


def add_firewall_rule_block_tcp_destination_port():
    """
    Add firewall rule to block outbound TCP traffic based on destination port 443 on map One to Default and priority 1500
    :return: None
    """

    # Set up firewall rule
    deny_destination_port_443_rule = {
                              "match": {
                                "acl": "",
                                "dst_port": "443"
                              },
                              "self": 1500,
                              "misc": {
                                "rule": "enable",
                                "logging": "disable",
                                "logging_priority": "0",
                                "tag": "iTest"
                              },
                              "comment": "iTest deny TCP traffic by destination port 443",
                              "gms_marked": False,
                              "set": {
                                "action": "deny"
                              }
                            }

    # Get current firewall rules AKA security policies to Silverpeak
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add rule to security_policy_rules in map One to Default with priority 1500
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_destination_port_443_rule

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


def remove_firewall_rule_block_tcp_destination_port():
    """
    Remove firewall rule to block outbound TCP traffic based on destination port 443 on map One to Default and priority 1500
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
    add_firewall_rule_block_tcp_destination_port()
