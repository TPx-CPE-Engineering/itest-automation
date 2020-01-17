#!/usr/bin/env python3
from velocloud.models import *
from Login.operator_login import api as vc_api

# Globals
EDGE_ID = None
ENTERPRISE_ID = None


def set_globals(edge_id, enterprise_id) -> None:
    global EDGE_ID, ENTERPRISE_ID
    EDGE_ID = int(edge_id)
    ENTERPRISE_ID = int(enterprise_id)


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


def main():
    print('hello')


if __name__ == '__main__':
    main()
