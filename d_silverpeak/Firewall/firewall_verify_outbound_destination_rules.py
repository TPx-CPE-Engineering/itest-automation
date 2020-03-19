from my_silverpeak import operator_login
from my_silverpeak.base_edge import SPBaseEdge
import json

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/18/2020

Test Case: ZB Firewall - Verify outbound IPaddr destination rules (NAT)
Expectations: Configured traffic not allowed through firewall
Usage: Configure outbound rule to deny all traffic based on destination address (Configuration > Templates > Default Template > Security Policies
    > Click on Zone (One to Default) in Matrix > Add Rule > Priority 1500 > Match Criteria "Destination IP" > 
    "4.2.2.2"; Verify unable to ping 4.2.2.2 from CPE)
"""

# Login as Operator
sp = operator_login.login()


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)


Edge: SPEdge


def add_firewall_outbound_rule_with_destination_ip(destination_ip):
    """
    Adds a firewall rule to zone One to Default with priority 1500 to block outbound traffic to destination ip
    :param destination_ip: IP address to block outbound traffic to
    :return: None
    """

    # Add subnet to destination ip
    destination_ip += "/24"

    # Setup Deny Source Address rule
    # TODO change action to deny once you want to truly test
    deny_source_address_rule = {"match": {"acl": "",
                                          "dst_ip": destination_ip
                                          },
                                "self": 1500,
                                "misc": {"rule": "enable",
                                         "logging": "disable",
                                         "logging_priority": "0",
                                         "tag": "iTest"
                                         },
                                "comment": "iTest deny outbound traffic to destination IP {}".format(destination_ip),
                                "gms_marked": False,
                                "set": {"action": "allow"
                                        }
                                }

    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=Edge.edge_id).data

    # Add new rule to Security Policy Rules
    # Add to 12_0 since that is 'One to Default'
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_source_address_rule

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = sp.post_sec_policy(applianceID=Edge.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        d = {'error': None, 'rows': 1}
        print(d)
    else:
        d = {'error': result.error, 'rows': 0}
        print(d)


def remove_firewall_outbound_rule_with_destination_ip(destination_ip):
    """
    Remove firewall rule in One to Default zone with priority 1500
    :param destination_ip: Not needed for Silver Peak but kept to reuse iTest test case
    :return: None
    """

    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=Edge.edge_id).data

    # Delete rule
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        print("Deny destination address rule not found")
        return

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = sp.post_sec_policy(applianceID=Edge.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        d = {'error': None, 'rows': 1}
        print(d)
    else:
        d = {'error': result.error, 'rows': 0}
        print(d)


def is_firewall_outbound_rule_with_destination_ip_present(destination_ip):
    """
    Prints yes or no (in json format) whether the firewall rule in One to Default with priority 1500 exists
    :param destination_ip: Not needed for Silver Peak but kept to reuse iTest test case
    :return: None
    """
    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=Edge.edge_id).data

    # Attempt to get Zone base Firewall rule with priority 1500 on One to Default zone
    deny_source_address_rule = security_policy_rules.get('map1', None).get('12_0', None).get('prio', None).get('1500', None)

    # Checking rule...
    if not deny_source_address_rule:
        # If rule is None, then rule does not exists
        print({"is_firewall_outbound_rule_with_destination_ip_present": 'no'})
    else:
        # If rule is not None, then rule exist
        print({"is_firewall_outbound_rule_with_destination_ip_present": 'yes'})


def set_globals(edge_id: str, enterprise_id: str, ssh_port: str):
    """
    Creates Silver Peak Edge object
    :param edge_id: Silver Peak Edge ID
    :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
    :param ssh_port: SSH Port for CPE sitting behind Silver Peak Edge
    :return: None
    """
    global Edge
    Edge = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=ssh_port)


if __name__ == '__main__':
    set_globals(edge_id='7.NE', enterprise_id='0', ssh_port="2201")
    is_firewall_outbound_rule_with_destination_ip_present(destination_ip='1.1.1.1')
    # add_firewall_outbound_rule_with_destination_ip(destination_ip='1.1.1.1')
    remove_firewall_outbound_rule_with_destination_ip(destination_ip='1.1.1.1')