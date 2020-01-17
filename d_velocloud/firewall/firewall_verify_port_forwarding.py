#!/usr/bin/env python3
from velocloud.models import *
from login.operator_login import api as vc_api

# Globals
EDGE_ID = None
ENTERPRISE_ID = None
SSH_PORT = None
SSH_RULE = None


def set_globals(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT
    EDGE_ID = int(edge_id)
    ENTERPRISE_ID = int(enterprise_id)
    SSH_PORT = int(ssh_port)


def is_ssh_rule_present() -> None:
    """
    Check if edge contains the SSH Port Forwarding rule

    """
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT

    d = {'is_ssh_rule_present': None}

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = get_module_from_edge_specific_profile(module_name='firewall')
    # Loop through inbound rules and check for a rule that has the following conditions:
    # 1. 'itest' is in the rule's name
    # 2. Rule's WAN Ports match ssh_port
    # 3. Rule's LAN Port is 22
    # If there is a rule with the above conditions, ssh rule exists
    # else ssh rule does not exists
    for rule in firewall_module.data['inbound']:
        if 'itest' in rule['name'].lower() and rule['action']['nat']['lan_port'] == 22 and rule['match'][
           'dport_high'] == SSH_PORT and rule['match']['dport_low'] == SSH_PORT:
            d['is_ssh_rule_present'] = 'yes'
            print(d)
            return

    d['is_ssh_rule_present'] = 'no'
    print(d)
    return


def remove_ssh_rule() -> None:
    """
    Remove SSH rule

    Removes SSH
    SSH rule is saved before removing into the SSH_RULE global variable
    """
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT, SSH_RULE

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = get_module_from_edge_specific_profile(module_name='firewall')

    for rule in firewall_module.data['inbound']:
        if 'itest' in rule['name'].lower() and rule['action']['nat']['lan_port'] == 22 and rule['match'][
           'dport_high'] == SSH_PORT and rule['match']['dport_low'] == SSH_PORT:
            SSH_RULE = rule
            firewall_module.data['inbound'].remove(rule)

    param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=ENTERPRISE_ID,
                                                   update=firewall_module)

    res = vc_api.configurationUpdateConfigurationModule(param)
    print(res)


def add_ssh_rule() -> None:
    """
    Add SSH rule back into the edge

    SSH rule is saved in the SSH_RULE global variable when it was removed
    """
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT, SSH_RULE

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = get_module_from_edge_specific_profile(module_name='firewall')

    firewall_module.data['inbound'].append(SSH_RULE)

    param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=ENTERPRISE_ID,
                                                   update=firewall_module)

    res = vc_api.configurationUpdateConfigurationModule(param)
    print(res)


def get_module_from_edge_specific_profile(module_name: str) -> ConfigurationModule:
    """
    Return a specific module from Edge's edge specific profile

    Possible modules: controlPlane, deviceSettings, firewall, QOS, WAN

    Enter the name of the module you want to get in module_name

    Returns empty ConfigurationModule if module is not found
    """
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT

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
