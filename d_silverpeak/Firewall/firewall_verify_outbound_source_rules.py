from my_silverpeak import operator_login
from my_silverpeak.base_edge import SPBaseEdge
import json

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/17/2020

Test Case: ZB Firewall - Verify outbound IPaddr source rules (NAT)
Expectations: Configured traffic not allowed through firewall
Usage: Configure outbound rule to deny all traffic based on source address (Configuration > Templates > Default Template > Security Policies >
    Click on Zone (One to Default) in Matrix > Add Rule > Priority 1500 > Match Criteria "Source IP" > "CPE IP Address"
    Verify any traffic from CPE is dropped
"""

# Login as Operator
sp = operator_login.login()


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)


EDGE: SPEdge


def set_globals(edge_id: str, enterprise_id: str, ssh_port: str):
    """
    Creates Silver Peak Edge object
    :param edge_id: Silver Peak Edge ID
    :param enterprise_id: Not needed for Silver Peak but kept to reuse iTest test case
    :param ssh_port: SSH Port for CPE sitting behind Silver Peak Edge
    :return: None
    """
    global EDGE
    EDGE = SPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=ssh_port)


def get_cpe_lan_ip() -> str:
    """
    Get the CPE's LAN IP (sitting behind Silverpeak Edge) by looking at the port forwarding rules and basing it on port, protocol, and comment
    :return: CPE LAN IP or an empty str
    """

    # Get Port Forwarding Rules
    url = sp.base_url + '/portForwarding/' + EDGE.edge_id
    res = sp._get(sp.session, url=url, headers=None, timeout=10)
    port_forwarding_rules = res.data

    # Locate the SSH Port Forwarding Rules based on it its protocol destination port and it has itest in the comments
    for rule in port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == EDGE.ssh_port and 'itest' in rule['comment'].lower():
            return rule['targetIp']

    # If rule is not found then raise a KeyError
    raise KeyError("A SSH Inbound Forwarding Rule with Protocol = TCP, Destination Port = {}, and string 'itest' in the Comment was not found.".format(
        EDGE.ssh_port))


def add_deny_source_address_rule() -> None:
    """
    Add a firewall rule to block traffic from source ip: CPE IP on zone One to Default with priority 1500
    """
    # Get LAN IP of CPE behind Silverpeak
    cpe_lan_ip = get_cpe_lan_ip()

    # Add subnet
    cpe_lan_ip = cpe_lan_ip + '/32'

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

    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add new rule to Security Policy Rules
    # Add to 12_0 since that is 'One to Default'
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_source_address_rule

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = sp.post_sec_policy(applianceID=EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        d = {'error': None, 'rows': 1}
        print(d)
    else:
        d = {'error': result.error, 'rows': 0}
        print(d)


def remove_deny_source_address_rule():
    """
    Remove firewall rule to block traffic from source ip: CPE IP which is on zone One to Default with priority 1500
    :return:
    """
    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=EDGE.edge_id).data

    # Delete rule
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        print("Deny source address rule not found")
        return

    # Setup Data for API call
    data = {"data": security_policy_rules, "options": {"merge": False, "templateApply": False}}
    data = json.dumps(data)

    # Call API call
    result = sp.post_sec_policy(applianceID=EDGE.edge_id, secPolData=data)

    # Check results
    if result.status_code == 204:
        d = {'error': None, 'rows': 1}
        print(d)
    else:
        d = {'error': result.error, 'rows': 0}
        print(d)


def is_deny_source_address_rule_present():
    """
    Prints yes or no (in json format) whether firewall rule to block traffic from source ip: CPE IP on zone One to Default with priority 1500 is present
    :return:
    """
    # Get Edge's Security Policy Rules data
    security_policy_rules = sp.get_sec_policy(applianceID=EDGE.edge_id).data

    deny_source_address_rule = security_policy_rules.get('map1', None).get('12_0', None).get('prio', None).get('1500', None)

    if not deny_source_address_rule:
        print({"is deny source address rule present": 'no'})
    else:
        print({"is deny source address rule present": 'yes'})


if __name__ == '__main__':
    set_globals(edge_id='7.NE', enterprise_id='0', ssh_port="2201")
    # add_deny_source_address_rule()
    # is_deny_source_address_rule_present()
    # remove_deny_source_address_rule()
