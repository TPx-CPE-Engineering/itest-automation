from my_silverpeak.base_edge import SPBaseEdge
import json
import time

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/19/2020

Test Case:      ZB Firewall - Verify outbound IPaddr source rules (NAT) (ACL)
Expectations:   Configured traffic not allowed through firewall
Usage:          Configure outbound ACL to deny all traffic based on source ip address = CPE's LAN IP. 
                ACL entry should already be be configured. If not:
                Templates > Default Template Group > Access Lists > Add ACL > ACL Name: "ONE-source_ip" > Add
                Create Rules: (Priority 1000 "CPE LAN IP" and permit) (Priority 1010 Match Everything and deny) 
                See Test Plan Instruction page for further details. 
                Add a firewall rule in Security Policies with match criteria set to ACL "ONE-source_ip"
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


def add_firewall_rule_deny_source_ip_acl() -> None:
    """
    Add firewall rule to deny outbound traffic to CPE LAN IP with a "ONE-source_ip" match ACL criteria and priority of 1500 on "One to Default" map
    :return: None
    """

    # Get LAN IP of CPE behind Silverpeak and Add subnet
    cpe_lan_ip = EDGE.get_cpe_lan_ip() + '/32'

    # Setup Deny Source Address rule
    deny_source_ip_rule_acl = {"match": {"acl": "ONE-source_ip",
                                         },
                               "self": 1500,
                               "misc": {"rule": "enable",
                                        "logging": "disable",
                                        "logging_priority": "0",
                                        "tag": "iTest"
                                        },
                               "comment": "iTest deny outbound traffic from source IP: {} (CPE LAN IP) (ACL)".format(cpe_lan_ip),
                               "gms_marked": False,
                               "set": {"action": "deny"
                                       }
                               }

    deny_source_address_rule2 = {
                                  "self": "12_12",
                                  "prio": {
                                    "1500": {
                                      "match": {
                                        "acl": "ONE-source_ip",
                                      },
                                      "self": 1500,
                                      "misc": {
                                        "rule": "enable",
                                        "logging": "disable",
                                        "logging_priority": "0",
                                        "tag": "iTest"
                                      },
                                      "comment": "iTest deny outbound traffic from source IP: {} (CPE LAN IP) (ACL)".format(cpe_lan_ip),
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
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add firewall rule to Security Policy Rules
    # Add to 12_0 since that is 'One to Default' with priority of 1500
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_source_ip_rule_acl

    # Add to zones 'ONE to ONE' (12_12)
    security_policy_rules['map1']['12_12'] = deny_source_address_rule2

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


def remove_firewall_rule_deny_source_ip_acl():
    """
    Remove firewall rule to deny outbound traffic to CPE LAN IP with a "ONE-source_ip" match ACL criteria and priority of 1500 on "One to Default" map
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
        time.sleep(10)
        EDGE.reset_port_flow(port=5060)
    else:
        print({'error': result.error, 'rows': 0})


def is_acl_source_ip_entry_present():
    """
    Prints yes or no (in json format) whether ACL entry named "ONE-source_ip", 1000 priority, with cpe lan ip as source ip exists
    :return: None
    """

    # Get current ACL entries
    acl_entries = EDGE.api._get(session=EDGE.api.session, url=EDGE.api.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data

    # Attempt to get "ONE-source_ip" ACL entry
    acl_one_source_ip_entry = acl_entries.get('ONE-source_ip', None)

    if acl_one_source_ip_entry:
        acl_one_source_ip = acl_one_source_ip_entry.get('entry', None).get('1000', None).get('src_ip', None)
        cpe_lan_ip = EDGE.get_cpe_lan_ip() + '/32'

        if acl_one_source_ip == cpe_lan_ip:
            # print({'response': 'yes'})
            print('yes')
        else:
            # print({'response': 'no'})
            print('no')
    else:
        # print({'response': 'no'})
        print('no')

# def add_acl_source_ip_entry():
#     """
#     Add a ACL entry named "ONE-source_ip" to Edge to deny all traffic based on source address.
#
#     (Templates > Default Template Group > Access Lists > Add ACL > "ACL Name" > Add)
#     Create Rules (Priority 1000 "Source IP" and permit) (Priority 1010 Match Everything and deny)
#     :return: None
#     """
#
#     # Get LAN IP of CPE behind Silverpeak and add Subnet
#     cpe_lan_ip = EDGE.get_cpe_lan_ip() + '/32'
#
#     # Set up ACL entry
#     acl_entry = {
#                     "entry": {
#                         "1000": {
#                             "permit": True,
#                             "comment": "iTest Source IP block",
#                             "src_ip": cpe_lan_ip
#                         },
#                         "1010": {
#                             "permit": False,
#                             "comment": "iTest Source IP block",
#                             "gms_marked": False
#                         }
#                     }
#                  }
#
#     # Get current ACL entries
#     acls = EDGE.api._get(session=EDGE.api.session, url=EDGE.api.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data
#
#     # Check if the entry we are entering is already in the current ACL entries
#     one_acl = acls.get('ONE-source_ip', None)
#
#     if one_acl:
#         # ACL already exists
#         return
#
#     # ACL does not exists so continue to add
#
#     # Add ACL
#     acls['ONE-source_ip'] = acl_entry
#
#     # Setup Data for API call
#     data = {"data": acls, "options": {"merge": False, "delDependent": True}}
#     data = json.dumps(data)
#
#     # Perform call
#     url = EDGE.api.base_url + '/appliance/rest/' + EDGE.edge_id + '/acls'
#     res = EDGE.api._post(session=EDGE.api.session, url=url, data=data)
#
#     # Check response status code
#     if res.status_code == 200:
#         print({'call': 'add_acl_source_ip_entry', 'error': None, 'rows': 1})
#     else:
#         print({'call': 'add_acl_source_ip_entry', 'error': res.error, 'rows': 0})
#
#
# def remove_acl_source_ip_entry():
#     """
#     Remove ACL entry named "ONE-source_ip" to Edge to deny all traffic based on source address.
#     :return: None
#     """
#
#     # Get current ACL entries
#     acl_entries = EDGE.api._get(session=EDGE.api.session, url=EDGE.api.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data
#
#     # Delete ONE-source_ip from acl entries
#     try:
#         del acl_entries['ONE-source_ip']
#     except KeyError:
#         # If KeyError then entry does not exists therefore you can say rule was successfully removed
#         print({'call': 'remove_acl_source_ip_entry', 'error': None, 'rows': 0})
#         return
#
#     # Setup Data for API call
#     data = {"data": acl_entries, "options": {"merge": False, "delDependent": True}}
#     data = json.dumps(data)
#
#     # Perform call
#     url = EDGE.api.base_url + '/appliance/rest/' + EDGE.edge_id + '/acls'
#     res = EDGE.api._post(session=EDGE.api.session, url=url, data=data)
#
#     # Check response status code
#     if res.status_code == 200:
#         print({'call': 'remove_acl_source_ip_entry', 'error': None, 'rows': 1})
#     else:
#         print({'call': 'remove_acl_source_ip_entry', 'error': res.error, 'rows': 0})


if __name__ == '__main__':
    create_edge(edge_id='18.NE', enterprise_id='0', ssh_port="2203")
