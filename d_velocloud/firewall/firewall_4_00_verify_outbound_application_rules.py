# from velocloud.models import *
# from my_velocloud.BaseEdge import BaseEdge
from my_velocloud.VelocloudEdge import VeloCloudEdge, Globals
# from velocloud import ConfigurationModule

# Globals
# EDGE: BaseEdge
DUT_EDGE: VeloCloudEdge


# class Edge(BaseEdge):
#     def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
#         super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
#
#
# def set_globals(edge_id, enterprise_id) -> None:
#     global EDGE
#     EDGE = Edge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0)
#
#
# def is_icmp_block_outbound_app_rule_present_old():
#     """
#     Checking if the Outbound Application rule to block ICMP traffic is present
#
#     The rule will be within the 'Voice' segment in the edge's firewall data and will be named 'iTest ICMP Block'
#     """
#
#     global EDGE
#
#     d = {'is_outbound_application_rule_present': None}
#
#     edges_firewall = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     voice_segment_outbound_rules = None
#
#     for seg in edges_firewall.data['segments']:
#         if seg['segment']['name'] == 'Voice':
#             voice_segment_outbound_rules = seg['outbound']
#
#     for rule in voice_segment_outbound_rules:
#         if rule['name'] == 'iTest ICMP Block':
#             d['is_outbound_application_rule_present'] = 'yes'
#             print(d)
#             return
#
#     d['is_outbound_application_rule_present'] = 'no'
#     print(d)
#     return
#
#
# def add_icmp_block_outbound_app_rule_old():
#     """
#     Adds an Outbound Application rule to block ICMP traffic
#
#     Adds the rule into the Voice segment. If no Voice segment is found then an error will print out and exit
#     """
#     global EDGE
#
#     icmp_block_rule = {
#                       "name": "iTest ICMP Block",
#                       "match": {
#                                 "appid": 70,
#                                 "classid": -1,
#                                 "dscp": -1,
#                                 "sip": "any",
#                                 "smac": "any",
#                                 "sport_high": -1,
#                                 "sport_low": -1,
#                                 "ssm": "255.255.255.255",
#                                 "svlan": -1,
#                                 "os_version": -1,
#                                 "hostname": "",
#                                 "dip": "any",
#                                 "dport_low": -1,
#                                 "dport_high": -1,
#                                 "dsm": "255.255.255.255",
#                                 "dvlan": -1,
#                                 "proto": -1,
#                                 "s_rule_type": "prefix",
#                                 "d_rule_type": "prefix"
#                                 },
#                       "action": {
#                                 "allow_or_deny": "deny"
#                                 },
#                       "loggingEnabled": "False"
#                       }
#
#     firewall_module = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     # Locate Voice segment
#     # Append rule to segment
#     # Push change
#     for seg in firewall_module.data['segments']:
#         if seg['segment']['name'] == 'Voice':
#             seg['outbound'].append(icmp_block_rule)
#             param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=EDGE.enterprise_id,
#                                                            update=ConfigurationModule(data=firewall_module.data))
#
#             res = EDGE.api.configurationUpdateConfigurationModule(param)
#             print(res)
#             return
#
#     # Error out if no 'Voice segment is found'
#     d = {'error': 'No Voice Segment found', 'rows': 0}
#     print(d)
#     exit()
#
#
# def remove_icmp_block_outbound_app_rule_old():
#     """
#     Removes an Outbound Application rule named 'iTest ICMP Block'
#
#     Looks through the Outbound Application rules and removes the rule we added when add_icmp_block_outbound_app_rule
#     was called.
#     """
#     global EDGE
#
#     voice_segment_name = 'Voice'
#     icmp_block_rule_name = 'iTest ICMP Block'
#
#     firewall_module = EDGE.get_module_from_edge_specific_profile(module_name="firewall")
#
#     # Locate Voice segment
#     # Remove rule from segment
#     # Push change
#     for seg in firewall_module.data['segments']:
#         if seg['segment']['name'] == voice_segment_name:
#             for rule in seg['outbound']:
#                 if rule['name'] == icmp_block_rule_name:
#                     seg['outbound'].remove(rule)
#                     param = ConfigurationUpdateConfigurationModule(id=firewall_module.id,
#                                                                    enterpriseId=EDGE.enterprise_id,
#                                                                    update=ConfigurationModule(data=firewall_module.data))
#                     res = EDGE.api.configurationUpdateConfigurationModule(param)
#                     print(res)
#                     return
#
#     # Error out if no 'Voice' segment is found
#     d = {'error': 'No Voice Segment found', 'rows': 0}
#     print(d)
#     exit()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)


def add_icmp_block_outbound_app_rule():
    icmp_block_rule = {
                      "name": "iTest ICMP Block",
                      "match": {
                                "appid": 70,
                                "classid": -1,
                                "dscp": -1,
                                "sip": "any",
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
                      "loggingEnabled": "False"
                      }

    print(DUT_EDGE.add_firewall_rule_to_segment(firewall_rule=icmp_block_rule,
                                                segment_name=Globals.VOICE_SEGMENT_NAME))


def remove_icmp_block_outbound_app_rule():
    print(DUT_EDGE.remove_firewall_rule_from_segment(firewall_rule_name='iTest ICMP Block',
                                                     segment_name=Globals.VOICE_SEGMENT_NAME))


if __name__ == '__main__':
    create_edge(edge_id='4', enterprise_id='1')
    remove_icmp_block_outbound_app_rule()
