#!/usr/bin/env python3
from velocloud.models import *
from login.operator_login import velocloud_api as vc_api

# Globals
EDGE_ID = None
ENTERPRISE_ID = None


def set_globals(edge_id, enterprise_id) -> None:
    global EDGE_ID, ENTERPRISE_ID
    EDGE_ID = int(edge_id)
    ENTERPRISE_ID = int(enterprise_id)


def is_icmp_block_outbound_app_rule_present():
    """
    Checking if the Outbound Application rule to block ICMP traffic is present

    The rule will be within the 'Voice' segment in the edge's firewall data and will be named 'iTest ICMP Block'
    """

    global EDGE_ID, ENTERPRISE_ID

    d = {'is_outbound_application_rule_present': None}

    edges_firewall = get_module_from_edge_specific_profile(module_name="firewall")

    voice_segment_outbound_rules = None

    for seg in edges_firewall.data['segments']:
        if seg['segment']['name'] == 'Voice':
            voice_segment_outbound_rules = seg['outbound']

    for rule in voice_segment_outbound_rules:
        if rule['name'] == 'iTest ICMP Block':
            d['is_outbound_application_rule_present'] = 'yes'
            print(d)
            return

    d['is_outbound_application_rule_present'] = 'no'
    print(d)
    return


def add_icmp_block_outbound_app_rule():
    """
    Adds an Outbound Application rule to block ICMP traffic

    Adds the rule into the Voice segment. If no Voice segment is found then an error will print out and exit
    """
    global EDGE_ID, ENTERPRISE_ID

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

    firewall_module = get_module_from_edge_specific_profile(module_name="firewall")

    # Locate Voice segment
    # Append rule to segment
    # Push change
    for seg in firewall_module.data['segments']:
        if seg['segment']['name'] == 'Voice':
            seg['outbound'].append(icmp_block_rule)
            param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=ENTERPRISE_ID,
                                                           update=firewall_module)

            res = vc_api.configurationUpdateConfigurationModule(param)
            print(res)
            return

    # Error out if no 'Voice segment is found'
    d = {'error': 'No Voice Segment found', 'rows': 0}
    print(d)
    exit()


def remove_icmp_block_outbound_app_rule():
    """
    Removes an Outbound Application rule named 'iTest ICMP Block'

    Looks through the Outbound Application rules and removes the rule we added when add_icmp_block_outbound_app_rule
    was called.
    """
    global EDGE_ID, ENTERPRISE_ID

    voice_segment_name = 'Voice'
    icmp_block_rule_name = 'iTest ICMP Block'

    firewall_module = get_module_from_edge_specific_profile(module_name="firewall")

    # Locate Voice segment
    # Remove rule from segment
    # Push change
    for seg in firewall_module.data['segments']:
        if seg['segment']['name'] == voice_segment_name:
            for rule in seg['outbound']:
                if rule['name'] == icmp_block_rule_name:
                    seg['outbound'].remove(rule)
                    param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=ENTERPRISE_ID,
                                                                   update=firewall_module)
                    res = vc_api.configurationUpdateConfigurationModule(param)
                    print(res)
                    return

    # Error out if no 'Voice' segment is found
    d = {'error': 'No Voice Segment found', 'rows': 0}
    print(d)
    exit()


def get_module_from_edge_specific_profile(module_name: str) -> ConfigurationModule:
    """
    Return a specific module from Edge's edge specific profile

    Possible modules: controlPlane, deviceSettings, firewall, QOS, WAN

    Enter the name of the module you want to get in module_name

    Returns empty ConfigurationModule if module is not found
    """
    global EDGE_ID, ENTERPRISE_ID

    # Get Config Stack
    param = EdgeGetEdgeConfigurationStack(edgeId=EDGE_ID, enterpriseId=ENTERPRISE_ID)
    config_stack = vc_api.edgeGetEdgeConfigurationStack(param)

    # Config Stack consists of 2 Profiles. Edge Specific Profile is in index 0 and Enterprise Profile is in index 1
    # Get Edge Specific Profile
    edge_specific_profile: EdgeGetEdgeConfigurationStackResultItem = config_stack[0]

    for module in edge_specific_profile.modules:
        if module.name == module_name:
            return module

    return ConfigurationModule()
