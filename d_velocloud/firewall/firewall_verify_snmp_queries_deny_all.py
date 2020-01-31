#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge

"""
Test Case: Verify SNMP queries to the Edge, are denied if SNMP deny all is configured
Expected Results: All SNMP queries dropped
Usage: Configure firewall to deny all SNMP traffic (default) and attempt to get a response through snmpwalk

Details:
Add a port forwarding rule SNMP 1161 -> 161 using CPE's LAN IP
Test 
"""


class FirewallSNMPEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, public_ip: str,  ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
        self.public_ip = public_ip

    def is_snmp_settings_v2c_enabled(self) -> None:
        """
        Prints yes or no (in json format) whether Edge has snmp version v2c enabled within Device -> SNMP Settings

        SNMP Settings can be found within the Edge's Device tab
        """
        d = {"is_snmp_settings_v2c_enabled": 'no'}

        # Get Edge's Edge Specific Device Settings module
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get is snmpv2c enabled value from Device Settings module
        try:
            is_snmp_enabled = device_settings_module.data['snmp']['snmpv2c']['enabled']
            if is_snmp_enabled:
                d["is_snmp_settings_v2c_enabled"] = 'yes'
                print(d)
                return
            else:
                print(d)
                return
        except KeyError:
            print(d)
            return

    def is_snmp_access_set_to_deny_all(self) -> None:
        """
        Prints yes or no (in json format) whether Edge has snmp access set to 'Deny All' within Firewall -> SNMP Access

        SNMP Access can be found within the Edge's Firewall tab
        """
        d = {"is_snmp_access_set_to_deny_all": 'no'}

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # 'Deny All' is set only when snmp access is not enabled
        try:
            if not firewall_module.data['services']['snmp']['enabled']:
                d["is_snmp_access_set_to_deny_all"] = 'yes'
                print(d)
                return
            else:
                print(d)
                return
        except KeyError:
            print(d)
            return

    def set_snmp_access_to_deny_all(self) -> None:
        """
        Sets the Edge's Firewall SNMP Access to 'Deny All'

        SNMP Access can be found within the Edge's Firewall tab
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        try:
            firewall_module.data['services']['snmp']['enabled'] = False
        except KeyError:
            res = {'error': "KeyError trying to set snmp enabled to False", 'rows': '0'}
            print(res)
            return

        # Set api's parameters
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id, update=firewall_module)

        # Push change
        res = api.configurationUpdateConfigurationModule(param)

        # Print response
        print(res)


EDGE: FirewallSNMPEdge


def is_snmp_settings_v2c_enabled() -> None:
    EDGE.is_snmp_settings_v2c_enabled()


def is_snmp_access_set_to_deny_all() -> None:
    EDGE.is_snmp_access_set_to_deny_all()


def set_snmp_access_to_deny_all() -> None:
    EDGE.set_snmp_access_to_deny_all()


def set_globals(edge_id, enterprise_id, ssh_port, public_ip) -> None:
    global EDGE
    EDGE = FirewallSNMPEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port), public_ip=public_ip)


if __name__ == '__main__':
    set_globals(edge_id=4, enterprise_id=1, ssh_port=2201, public_ip="216.241.61.7")