#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge

"""
Test Case: Verify SNMP queries are denied if SNMP deny all is configured
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

    def get_wan_link(self) -> dict:
        """
        Gets the Edge's WAN link information that matches the Edge's public ip
        """

        # Get all the Edge's wan links
        # Within the GUI, this information is found in the Device -> WAN Settings
        wan_links = self.get_wan_settings_links()

        # Search through the wan links and find the link that has the same Public IP as the Edge's public ip
        for wan_link in wan_links:
            if wan_link['publicIpAddress'] == self.public_ip:
                return wan_link

        # If no wan link found then return an empty dict
        return {}

    def add_snmp_port_forwarding_rule(self) -> None:
        """
        Adds a SNMP port forwarding rule named 'SNMP added by iTest'

        The rule will also have the following configured:
        Protocol: UDP
        Interface: use same interface CPE SSH port forwarding rule is on
        WAN Port: 1161
        LAN IP: CPE's LAN IP
        LAN Port: 22
        Segment: Voice
        """

        # Get CPE SSH Port Forwarding Rule
        # This rule holds information needed to add snmp port forwarding rule
        cpe_ssh_rule = self.get_cpe_ssh_port_forwarding_rule()

        # Set properties for snmp rule
        rule_name = 'SNMP added by iTest'
        rule_protocol = 17  # UDP Protocol
        rule_interface = cpe_ssh_rule['action']['interface']
        rule_wan_port = 1161
        rule_lan_ip = cpe_ssh_rule['action']['nat']['lan_ip']
        rule_lan_port = 161
        rule_segment_id = cpe_ssh_rule['action']['segmentId']

        # Set up snmp rule
        snmp_port_forwarding_rule = {
                                    "name": rule_name,
                                    "loggingEnabled": False,
                                    "match": {
                                              "appid": -1,
                                              "classid": -1,
                                              "dscp": -1,
                                              "sip": "any",
                                              "sport_high": -1,
                                              "sport_low": -1,
                                              "ssm": "any",
                                              "svlan": -1,
                                              "os_version": -1,
                                              "hostname": "",
                                              "dip": "any",
                                              "dport_low": rule_wan_port,
                                              "dport_high": rule_wan_port,
                                              "dsm": "any",
                                              "dvlan": -1,
                                              "proto": rule_protocol
                                            },
                                    "action": {
                                              "type": "port_forwarding",
                                              "segmentId": rule_segment_id,
                                              "nat": {
                                                    "lan_ip": rule_lan_ip,
                                                    "lan_port": rule_lan_port
                                                    },
                                              "interface": rule_interface,
                                              "subinterfaceId": -1
                                            }
                                    }

        # Get firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Add rule to firewall module
        firewall_module.data['inbound'].append(snmp_port_forwarding_rule)

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id, update=firewall_module)
        res = api.configurationUpdateConfigurationModule(param)
        print(res)

    def remove_snmp_port_forwarding_rule(self) -> None:
        """
        Removes SNMP port forwarding rule named 'SNMP added by iTest'

        Rule was added my add_snmp_port_forwarding_rule()
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Search through firewalls inbound rules and remove the rule named 'SNMP added by iTest'
        for inbound_rule in firewall_module.data['inbound']:
            if inbound_rule['name'] == 'SNMP added by iTest':
                firewall_module.data['inbound'].remove(inbound_rule)
                break

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id, update=firewall_module)
        res = api.configurationUpdateConfigurationModule(param)
        print(res)

    def is_snmp_port_forwarding_rule_present(self) -> None:
        """
        Prints yes or no (in json format) whether SNMP port forwarding rule named 'SNMP added by iTest' is present on the Edge

        Uses the name 'SNMP added by iTest' to check whether the snmp rule added by add_snmp_port_forwarding rule is
        present
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Search through firewalls inbound rules and remove the rule named 'SNMP added by iTest'
        for inbound_rule in firewall_module.data['inbound']:
            if inbound_rule['name'] == 'SNMP added by iTest':
                d = {'is_snmp_port_forwarding_rule_present': 'yes'}
                print(d)
                return

        d = {'is_snmp_port_forwarding_rule_present': 'no'}
        print(d)
        return

    def add_deny_snmp_firewall_rule(self) -> None:
        """
        Adds a firewall rule to deny all snmp traffic named "SNMP deny all added by iTest"
        """

        # Set properties for deny snmp firewall rule
        rule_name = "SNMP deny all added by iTest"
        rule_snmp_application_id = 190
        rule_action = 'deny'

        deny_snmp_rule = {
                            "name": rule_name,
                            "match": {
                                    "appid": rule_snmp_application_id,
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
                                "allow_or_deny": rule_action
                            },
                            "loggingEnabled": "False"
                            }

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get Voice Segment within Firewall module
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name, module=firewall_module)

        # Append snmp rule to Voice Segment Outbound Firewall Rules
        firewall_voice_segment['outbound'].append(deny_snmp_rule)

        # Set api parameters
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id, update=firewall_module)

        # Push change
        res = api.configurationUpdateConfigurationModule(param)

        # Print result
        print(res)
        return

    def remove_deny_snmp_firewall_rule(self):
        """
        Removes firewall rule added named "SNMP deny all added by iTest"

        Rule was added by add_deny_snmp_firewall_rule
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get Voice Segment within Firewall module
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name, module=firewall_module)

        # Search through Firewall Voice Segment to locate snmp rule, once found, remove rule
        for outbound_rule in firewall_voice_segment['outbound']:
            if outbound_rule['name'] == "SNMP deny all added by iTest":
                firewall_voice_segment['outbound'].remove(outbound_rule)
                break

        # Set api parameters
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id, update=firewall_module)

        # Push change
        res = api.configurationUpdateConfigurationModule(param)

        # Print result
        print(res)
        return

    def is_deny_snmp_firewall_rule_present(self):
        """
        Prints yes or no whether the firewall rule to deny snmp traffic named "SNMP deny all added by iTest" is present
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get Voice Segment within Firewall module
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name, module=firewall_module)

        # Search through Firewall Voice Segment to see if snmp rule is present
        for outbound_rule in firewall_voice_segment['outbound']:
            if outbound_rule['name'] == "SNMP deny all added by iTest":
                d = {"is_deny_snmp_firewall_rule_present": 'yes'}
                print(d)
                return

        d = {"is_deny_snmp_firewall_rule_present": 'no'}
        print(d)
        return


# Globals
EDGE: FirewallSNMPEdge


def add_snmp_port_forwarding_rule():
    EDGE.add_snmp_port_forwarding_rule()


def remove_snmp_port_forwarding_rule():
    EDGE.remove_snmp_port_forwarding_rule()


def is_snmp_port_forwarding_rule_present():
    EDGE.is_snmp_port_forwarding_rule_present()


def add_deny_snmp_firewall_rule():
    EDGE.add_deny_snmp_firewall_rule()


def remove_deny_snmp_firewall_rule():
    EDGE.remove_deny_snmp_firewall_rule()


def is_deny_snmp_firewall_rule_present():
    EDGE.is_deny_snmp_firewall_rule_present()


def set_globals(edge_id, enterprise_id, ssh_port, public_ip) -> None:
    global EDGE
    EDGE = FirewallSNMPEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port), public_ip=public_ip)


if __name__ == '__main__':
    set_globals(edge_id=4, enterprise_id=1, ssh_port=2201, public_ip="216.241.61.7")