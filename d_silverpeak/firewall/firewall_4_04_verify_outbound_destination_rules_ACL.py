from my_silverpeak.base_edge import SPBaseEdge
import json
import time

"""
Silver Peak Test Plan v2
General Edge Functions
ZB Firewall
Author: juan.brena@tpx.com
Date: 3/23/2020

Test Case:      ZB Firewall - Verify outbound IPaddr destination rules (NAT) (ACL)
Expectations:   Configured traffic not allowed through firewall
Usage:          Configure outbound ACL to deny all traffic based on destination ip address = '4.2.2.2'. 
                ACL entry should already be be configured. If not:
                Templates > Default Template Group > Access Lists > Add ACL > ACL Name: "ONE-destination_ip" > Add
                Create Rules: (Priority 1000 "Destination IP" and permit) (Priority 1010 Match Everything and deny) 
                See Test Plan Instruction page for further details. 
                Add a firewall rule in Security Policies with match criteria set to ACL "ONE-destination_ip"
"""


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)


EDGE: SPEdge
DESTINATION_IP_BLOCKED = '4.2.2.2'


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


def add_firewall_rule_deny_destination_ip_acl() -> None:
    """
    Add firewall rule to deny outbound traffic to DESTINATION_IP_BLOCKED with a "ONE-destination_ip" match criteria and priority of 1500 on "One to Default" map
    :return: None
    """

    # Setup Deny Destination Address rule with match criteria ONE_destination-ip
    deny_destination_ip_rule_acl = {"match": {"acl": "ONE-destination_ip",
                                              },
                                    "self": 1500,
                                    "misc": {"rule": "enable",
                                             "logging": "disable",
                                             "logging_priority": "0",
                                             "tag": "iTest"
                                             },
                                    "comment": "iTest deny outbound traffic to destination IP: {} (ACL)".format(DESTINATION_IP_BLOCKED),
                                    "gms_marked": False,
                                    "set": {"action": "deny"
                                            }
                                    }

    # Get Edge's Security Policy Rules data
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Add new firewall rule to Security Policy Rules
    # Add to 12_0 since that is 'One to Default' with a priority of 1500
    security_policy_rules['map1']['12_0']['prio']['1500'] = deny_destination_ip_rule_acl

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
        d = {'error': result.error, 'rows': 0}
        print(d)


def remove_firewall_rule_deny_destination_ip_acl():
    """
    Remove firewall rule to deny outbound traffic to DESTINATION_IP_BLOCKED with a "ONE-destination_ip" match criteria and priority of 1500 on "One to
    Default" map
    :return: None
    """

    # Get Edge's Security Policy Rules data
    security_policy_rules = EDGE.api.get_sec_policy(applianceID=EDGE.edge_id).data

    # Delete firewall rule on "One to Default" map and a priority of 1500
    try:
        del security_policy_rules['map1']['12_0']['prio']['1500']
    except KeyError:
        # If KeyError then entry does not exists therefore firewall rule was successfully removed
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


def is_acl_destination_ip_entry_present():
    """
    Prints yes or no (in json format) whether ACL entry named "ONE-destination_ip" with a 100 priority rule to permit DESTINATION_IP_BLOCKED exists
    :return: None
    """

    # Get current ACL entries
    acl_entries = EDGE.api._get(session=EDGE.api.session, url=EDGE.api.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data

    # Check if "ONE-destination_ip" ACL entry exists
    acl_one_destination_ip_entry = acl_entries.get('ONE-destination_ip', None)

    if acl_one_destination_ip_entry:
        acl_one_destination_ip = acl_one_destination_ip_entry.get('entry', None).get('1000', None).get('dst_ip', None)

        if acl_one_destination_ip == DESTINATION_IP_BLOCKED + '/32':
            print("yes")
        else:
            print("no")
    else:
        print("no")


# Functions to apply ACL but we are assuming they will already be configured
# def add_acl_source_ip_entry():
#     """
#     Add a ACL entry named "ONE-source_ip" to Edge to deny all traffic based on source address.
#
#     (Templates > Default Template Group > Access Lists > Add ACL > "ACL Name" > Add)
#     Create Rules (Priority 1000 "Source IP" and permit) (Priority 1010 Match Everything and deny)
#     :return: None
#     """
#
#     # Get LAN IP of CPE behind Silverpeak
#     cpe_lan_ip = get_cpe_lan_ip()
#
#     # Add subnet
#     cpe_lan_ip = cpe_lan_ip + '/32'
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
#     acls = sp._get(session=sp.session, url=sp.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data
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
#     url = sp.base_url + '/appliance/rest/' + EDGE.edge_id + '/acls'
#     res = sp._post(session=sp.session, url=url, data=data)
#
#     # Check response status code
#     if res.status_code == 200:
#         print({'call': 'add_acl_source_ip_entry', 'error': None, 'rows': 1})
#     else:
#         print({'call': 'add_acl_source_ip_entry', 'error': res.error, 'rows': 0})


# def remove_acl_source_ip_entry():
#     """
#     Remove ACL entry named "ONE-source_ip" to Edge to deny all traffic based on source address.
#     :return: None
#     """
#
#     # Get current ACL entries
#     acl_entries = sp._get(session=sp.session, url=sp.base_url + "/acls/" + EDGE.edge_id + "?cached=false").data
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
#     url = sp.base_url + '/appliance/rest/' + EDGE.edge_id + '/acls'
#     res = sp._post(session=sp.session, url=url, data=data)
#
#     # Check response status code
#     if res.status_code == 200:
#         print({'call': 'remove_acl_source_ip_entry', 'error': None, 'rows': 1})
#     else:
#         print({'call': 'remove_acl_source_ip_entry', 'error': res.error, 'rows': 0})


if __name__ == '__main__':
    create_edge(edge_id='7.NE', enterprise_id='0', ssh_port="2201")
    is_acl_destination_ip_entry_present()
