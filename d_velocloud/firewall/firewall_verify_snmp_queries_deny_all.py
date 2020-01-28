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
        Adds a port forwarding rule to the Edge to forward SNMP traffic

        Rule will have the following properties:
        Name: iTest SNMP
        Protocol: UDP
        Interface: Main Public Wired Interface
        WAN Port(s): 1161
        LAN IP: CPE's LAN IP
        LAN Port: 161
        Segment: Voice segment
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


    def remove_snmp_port_forwarding_rule(self):
        print('todo')

    def is_snmp_port_forwarding_rule_present(self):
        print('todo')

    def add_deny_snmp_firewall_rule(self):
        print('todo')

    def remove_deny_snmp_firewall_rule(self):
        print('todo')

    def is_deny_snmp_firewall_rule_present(self):
        print('todo')


# Globals
EDGE: FirewallSNMPEdge


def add_snmp_port_forwarding_rule():
    EDGE.add_snmp_port_forwarding_rule()


def remove_snmp_port_forwarding_rule():
    EDGE.add_snmp_port_forwarding_rule()


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
