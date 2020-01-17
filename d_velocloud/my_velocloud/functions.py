from velocloud.models import *
from login.operator_login import velocloud_api as vc_api

"""
This file contains functions that I re-use a lot when performing velocloud api calls
"""


def get_module_from_edge_specific_profile(module_name: str, edge_id: int, enterprise_id: int) -> ConfigurationModule:
    """
    Return a specific module from Edge's edge specific profile

    Possible modules: 'controlPlane', 'deviceSettings', 'firewall', 'QOS', 'WAN'
    Enter the name of the module you want to get in module_name

    Returns empty ConfigurationModule if module is not found
    """

    if not (module_name == 'controlPlane' or module_name == 'deviceSettings' or module_name == 'firewall' or
            module_name == 'QOS' or module_name == 'WAN'):
        print('Module name error. Module not one of the following: \'controlPlane\', \'devicesSettings\', \'firewall\','
              '\'QOS\', \'WAN\'. Your selection: {}'.format(module_name))

        return ConfigurationModule()

    # Get Config Stack
    param = EdgeGetEdgeConfigurationStack(edgeId=edge_id, enterpriseId=enterprise_id)
    config_stack = vc_api.edgeGetEdgeConfigurationStack(param)

    # Config Stack consists of 2 Profiles. Edge Specific Profile is in index 0 and Enterprise Profile is in index 1
    # Get Edge Specific Profile
    edge_specific_profile: EdgeGetEdgeConfigurationStackResultItem = config_stack[0]

    for module in edge_specific_profile.modules:
        if module.name == module_name:
            return module

    return ConfigurationModule()
