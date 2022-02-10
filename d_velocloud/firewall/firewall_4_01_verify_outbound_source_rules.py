# from velocloud.models import *
# from my_velocloud.BaseEdge import BaseEdge
from my_velocloud.VelocloudEdge import VeloCloudEdge, Globals

"""
Test case: Verify Outbound source rules

Expected Results: Configured traffic not allowed through firewall

Usage: Configure outbound rule to deny all traffic based on source address
"""

# class Edge(BaseEdge):
#     def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
#         super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)


DUT_EDGE: VeloCloudEdge


# def set_globals(edge_id, enterprise_id, ssh_port) -> None:
#     global EDGE
#     EDGE = Edge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


# def is_deny_source_address_rule_present() -> bool:
#     """
#     Checks the edge's firewall to see if the rule to block all CPE traffic is present
#
#     Looks through the edge's Voice segment outbound firewall rules for a rule that has the following conditions:
#     1. rule's name is 'iTest Block CPE Traffic'
#     2. rule's source IP (sip) equals CPE's IP
#     3. rule's action is to 'Deny'
#     A print statement in json format is displayed whether or not rule is present.
#
#     Entering Firewall module json structure like so...
#     --------------------------------------------------
#     Firewall:
#         data:
#             segments:
#                 voice_segment:
#                     outbound:
#                         CHECK FOR DENY SOURCE ADDRESS RULE HERE
#     """
#
#     # Get Edge's global variables
#     global EDGE
#
#     # Set name for Voice Segment
#     voice_segment_name = 'Voice'
#
#     # Set rule's properties
#     outbound_source_rule_name = 'iTest Block CPE Traffic'
#     outbound_source_rule_source_ip = get_cpe_lan_ip()
#     outbound_source_rule_action = 'deny'
#
#     # Get Edge's firewall module
#     edges_firewall = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     # Locate Voice Segment
#     voice_segment = None
#     for seg in edges_firewall.data['segments']:
#         if seg['segment']['name'] == voice_segment_name:
#             voice_segment = seg
#
#     # Search through the Voice segment to find the rule
#     for rule in voice_segment['outbound']:
#         if rule['name'] == outbound_source_rule_name and \
#                 rule['match']['sip'] == outbound_source_rule_source_ip and \
#                 rule['action']['allow_or_deny'] == outbound_source_rule_action:
#             d = {'is_deny_source_address_rule_present': 'yes'}
#             print(d)
#             return True
#
#     d = {'is_deny_source_address_rule_present': 'no'}
#     print(d)
#     return False


# def add_deny_source_address_rule_old() -> None:
#     """
#     Adds an outbound source rule to the edges firewall to block all traffic from CPE based on IP
#
#     Outbound source rule will be added to the Voice segment
#     Outbound source rule will have the following configuration:
#     1. name will be 'iTest Block CPE Traffic'
#     2. source ip will be CPE's IP
#     3. action will be 'deny'
#
#     Firewall module json structure
#     --------------------------------------------------
#     Firewall:
#         data:
#             segments:
#                 voice_segment:
#                     outbound:
#                         ADD DENY SOURCE ADDRESS RULE HERE
#     """
#
#     # Get Edge's global variables
#     global EDGE
#
#     # Voice segment name
#     voice_segment_name = 'Voice'
#
#     # Set rule's properties
#     outbound_source_rule_name = 'iTest Block CPE Traffic'
#     outbound_source_rule_ip = get_cpe_lan_ip()
#     outbound_source_rule_action = 'deny'
#
#     # Set rule with properties
#     outbound_source_rule = {
#         "name": outbound_source_rule_name,
#         "match": {
#             "appid": -1,
#             "classid": -1,
#             "dscp": -1,
#             "sip": outbound_source_rule_ip,
#             "smac": "any",
#             "sport_high": -1,
#             "sport_low": -1,
#             "ssm": "255.255.255.255",
#             "svlan": -1,
#             "os_version": -1,
#             "hostname": "",
#             "dip": "any",
#             "dport_low": -1,
#             "dport_high": -1,
#             "dsm": "255.255.255.255",
#             "dvlan": -1,
#             "proto": -1,
#             "s_rule_type": "prefix",
#             "d_rule_type": "prefix"
#         },
#         "action": {
#             "allow_or_deny": outbound_source_rule_action
#         },
#         "loggingEnabled": "False",
#     }
#
#     # Get edges firewall module
#     edges_firewall = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     # Find Voice segment
#     voice_segment = None
#     for seg in edges_firewall.data['segments']:
#         if seg['segment']['name'] == voice_segment_name:
#             voice_segment = seg
#
#     # Add rule to the Voice segment
#     voice_segment['outbound'].append(outbound_source_rule)
#
#     # Push change
#     param = ConfigurationUpdateConfigurationModule(id=edges_firewall.id, enterpriseId=EDGE.enterprise_id,
#                                                    update=ConfigurationModule(data=edges_firewall.data))
#     res = EDGE.api.configurationUpdateConfigurationModule(param)
#     print(res)


# def remove_deny_source_address_rule_old() -> None:
#     """
#     Removes an outbound source rule from the edges firewall that blocks all traffic from CPE based on IP
#
#     Rule will be removed from to the Voice segment
#     Rule will have the following configuration:
#     1. rule's name will be 'iTest Block CPE Traffic'
#     2. rule's source ip will be CPE's IP
#     3. rule's action will be 'deny'
#
#     Firewall module json structure
#     --------------------------------------------------
#     Firewall:
#         data:
#             segments:
#                 voice_segment:
#                     outbound:
#                         REMOVE DENY SOURCE ADDRESS RULE FROM HERE
#     """
#
#     # Get Edge's global variables
#     global EDGE
#
#     # Voice segment name
#     voice_segment_name = 'Voice'
#
#     # Set rule's properties
#     outbound_source_rule_name = 'iTest Block CPE Traffic'
#     outbound_source_rule_source_ip = get_cpe_lan_ip()
#     outbound_source_rule_action = 'deny'
#
#     # Get edges firewall module
#     edges_firewall = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     # Find Voice segment
#     voice_segment = None
#     for seg in edges_firewall.data['segments']:
#         if seg['segment']['name'] == voice_segment_name:
#             voice_segment = seg
#
#     # Find rule within Voice segment
#     # Remove rule
#     # Push change
#     for rule in voice_segment['outbound']:
#         if rule['name'] == outbound_source_rule_name and \
#                 rule['match']['sip'] == outbound_source_rule_source_ip and \
#                 rule['action']['allow_or_deny'] == outbound_source_rule_action:
#             voice_segment['outbound'].remove(rule)
#
#             param = ConfigurationUpdateConfigurationModule(id=edges_firewall.id, enterpriseId=EDGE.enterprise_id,
#                                                            update=ConfigurationModule(data=edges_firewall.data))
#             res = EDGE.api.configurationUpdateConfigurationModule(param)
#             print(res)
#             return
#
#     print('No deny source address rule found')

def create_edge(edge_id, enterprise_id, ssh_port):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id,
                             enterprise_id=enterprise_id,
                             cpe_ssh_port=ssh_port)


def get_cpe_lan_ip() -> str:
    """
    Gets the LAN IP of the CPE behind the edge

    Searches through the edge's inbound firewall rules for a rule that has the following conditions:
    1. rule's name has the keyword 'itest' in it
    2. rule's protocol is 'TCP'
    3. rule's WAN Ports equals global SSH_PORT
    4. rule's LAN Port is 22
    Once it finds such rule, it returns the rule's LAN IP which will be the CPE's IP
    :return: LAN IP
    """

    firewall = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    tcp = 6
    lan_port = 22

    for rule in firewall['data']['inbound']:
        if 'itest' in rule['name'].lower() and \
                rule['match']['proto'] == tcp and \
                rule['match']['dport_high'] == DUT_EDGE.cpe_ssh_port and \
                rule['match']['dport_low'] == DUT_EDGE.cpe_ssh_port and \
                rule['action']['nat']['lan_port'] == lan_port:
            return rule['action']['nat']['lan_ip']

    raise ValueError("Cannot find CPE's LAN IP by looking through firewall rules.")


def add_deny_source_address_rule():
    outbound_source_rule = {
        "name": 'iTest Block CPE Traffic',
        "match": {
            "appid": -1,
            "classid": -1,
            "dscp": -1,
            "sip": get_cpe_lan_ip(),
            "smac": "any",
            "sport_high": -1,
            "sport_low": -1,
            "ssm": "255.255.255.255",
            "svlan": -1,
            "os_version": -1,
            "hostname": "",
            "dip": "any",
            "dport_low": -1,
            "dport_high": -1,
            "dsm": "255.255.255.255",
            "dvlan": -1,
            "proto": -1,
            "s_rule_type": "prefix",
            "d_rule_type": "prefix"
        },
        "action": {
            "allow_or_deny": "deny"
        },
        "loggingEnabled": "False",
    }

    print(DUT_EDGE.add_firewall_rule_to_segment(firewall_rule=outbound_source_rule,
                                                segment_name=Globals.VOICE_SEGMENT_NAME))


def remove_deny_source_address_rule():
    print(DUT_EDGE.remove_firewall_rule_from_segment(firewall_rule_name='iTest Block CPE Traffic',
                                                     segment_name=Globals.VOICE_SEGMENT_NAME))


if __name__ == '__main__':
    create_edge(edge_id='239', enterprise_id='1', ssh_port="2201")
    remove_deny_source_address_rule()