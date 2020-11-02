from my_velocloud.VelocloudEdge import VeloCloudEdge

"""
Test Case: Verify SNMP queries to the Edge, are allowed if SNMP Access 'Allow the following IPs' is checked and 
configured.
Expected Results: Configured IP's will be allowed to send SNMP queries while all others be denied.
Usage: Confirm SNMP Settings v2c is enabled. Configure Edge's Firewall SNMP Access to 'Allow the following IPs

Details:
Ensure SNMP Settings v2c is enabled. You can find that in Edge's Device tab, scroll down to SNMP Settings. Port set to
161, community set to "tpc1n0c", and Allowed IPs: "Any" checked. 

Test by setting Edge's Firewall SNMP Access to "Allow the following IPs" and enter an IP you can ssh into. 
"""


# class FirewallSNMPQueriesEdge(BaseEdge):
#
#     def __init__(self, edge_id: int, enterprise_id: int, public_ip: str,  ssh_port: int):
#         super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
#         self.public_ip = public_ip
#
#     def are_snmp_settings_set(self):
#         """
#         Prints yes or no whether Edge's SNMP Settings (version v2c on port 161 with community string 'tpc1n0c') are set
#         """
#
#         # Get device module
#         device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')
#
#         # Get 'snmp' dict from device module data and check if the settings are set
#         snmp_data = device_settings_module.data['snmp']
#
#         # Check if SNMP Settings is set on Port 161
#         is_port_161 = False
#         if snmp_data['port'] == 161:
#             is_port_161 = True
#
#         # Check if SNMP Settings version v2c is enabled
#         is_snmpv2c_enabled = False
#         if snmp_data['snmpv2c']['enabled']:
#             is_snmpv2c_enabled = True
#
#         # Check if the community string is equal to 'tpc1n0c'
#         is_community_string_tpc1n0c = False
#         if snmp_data['snmpv2c']['community'] == 'tpc1n0c':
#             is_community_string_tpc1n0c = True
#
#         # Print results
#         if is_port_161 and is_snmpv2c_enabled and is_community_string_tpc1n0c:
#             d = {'are_snmp_settings_set': 'yes'}
#             print(d)
#         else:
#             d = {'are_snmp_settings_set': 'no', 'is_port_161': is_port_161, 'is_snmpv2c_enabled': is_snmpv2c_enabled,
#                  'is_community_string_tpc1n0c': is_community_string_tpc1n0c}
#             print(d)
#
#     def set_snmp_access_to_allow_ip(self, ip_allowed: str) -> None:
#         """
#         Sets Edge's SNMP Access configuration to allow an IP
#         """
#
#         # Get firewall module
#         firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')
#
#         # Get SNMP service
#         snmp_service = firewall_module.data['services']['snmp']
#
#         # Enable snmp
#         snmp_service['enabled'] = True
#
#         # Insert IP so it can be allowed
#         snmp_service['allowSelectedIp'].append(ip_allowed)
#
#         # Update firewall with updated snmp service
#         firewall_module.data['services']['snmp'] = snmp_service
#
#         # Set api parameters
#         param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id,
#                                                        update=ConfigurationModule(data=firewall_module.data))
#
#         # Push api call
#         res = self.api.configurationUpdateConfigurationModule(param)
#
#         # Print results
#         print(res)
#
#     def set_snmp_access_to_deny_all(self):
#         """
#         Sets Edge's SNMP Access configuration to allow an IP
#         """
#
#         # Get firewall module
#         firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')
#
#         # Get SNMP service data
#         snmp_service = firewall_module.data['services']['snmp']
#
#         # Disable snmp
#         snmp_service['enabled'] = False
#
#         # Clear allowed IPs
#         snmp_service['allowSelectedIp'] = []
#
#         # Update firewall with updated snmp service
#         firewall_module.data['services']['snmp'] = snmp_service
#
#         # Set api parameters
#         param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id,
#                                                        update=ConfigurationModule(data=firewall_module.data))
#
#         # Push api call
#         res = self.api.configurationUpdateConfigurationModule(param)
#
#         # Print results
#         print(res)
#
#     def is_snmp_access_set_to_deny_all(self) -> None:
#         """
#         Prints yes or no (in json format) whether Edge's Firewall SNMP Access is set to 'Deny All'
#         """
#         # Get firewall module
#         firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')
#
#         # Get SNMP service data
#         snmp_service = firewall_module.data['services']['snmp']
#
#         d = {'is_snmp_access_set_to_deny_all': 'unknown'}
#
#         # Check if SNMP is enabled or disabled
#         if not snmp_service['enabled']:
#             d = {'is_snmp_access_set_to_deny_all': 'yes'}
#         else:
#             d = {'is_snmp_access_set_to_deny_all': 'no'}
#
#         print(d)
#         return


DUT_EDGE: VeloCloudEdge
PUBLIC_IP: str


def create_edge(edge_id, enterprise_id, ssh_port, public_ip) -> None:
    global DUT_EDGE, PUBLIC_IP
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, cpe_ssh_port=ssh_port)
    PUBLIC_IP = public_ip

    print(DUT_EDGE.set_snmp_v2c_settings())


def set_snmp_access_to_deny_all():
    print(DUT_EDGE.set_snmp_access_to_deny_all())


def set_snmp_access_to_allow_ip(ip_allowed: str):
    """
    Sets Edge's SNMP Access configuration to allow an IP
    """

    # Get firewall module
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    # Get SNMP service
    snmp_service = firewall_module['data']['services']['snmp']

    # Enable snmp
    snmp_service['enabled'] = True

    # Insert IP so it can be allowed
    snmp_service['allowSelectedIp'].append(ip_allowed)

    # Update firewall with updated snmp service
    firewall_module['data']['services']['snmp'] = snmp_service

    print(DUT_EDGE.update_configuration_module(module=firewall_module))


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1, ssh_port=2201, public_ip='216.241.61.9')
    set_snmp_access_to_deny_all()