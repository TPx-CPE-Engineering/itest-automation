from velocloud.models import *
from my_velocloud.BaseEdge import BaseEdge

"""
Test Case: Verify 1:1 NAT
Expected Results: Verify CPE replies to a snmpwalk request when 1:1 NAT rule is enabled on the SD-WAN
Usage: Enable 1:1 NAT rule for CPE on SD-WAN, execute a snmpwalk request to the SD-WAN's public WAN IP, and 
verify CPE replies.
"""


class FirewallOneToOneNatEdge(BaseEdge):
    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int, public_ip: str):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
        self.public_ip = public_ip

        self.one_to_one_nat_rule_name = None
        self.one_to_one_nat_rule_outside_ip = None
        self.one_to_one_nat_rule_interface = None
        self.one_to_one_nat_rule_inside_ip = None
        self.one_to_one_nat_rule_segment_id = None
        self.set_one_to_one_nat_rule_properties()

    def set_one_to_one_nat_rule_properties(self) -> None:
        """
        Sets the properties needed to add the 1 to 1 nat firewall rule to the Edge

        The following properties are needed to add the 1 to 1 NAT rule:
        1. Name - The rule's name will be hardcoded to 'iTest 1 to 1 NAT'

        2. Outside IP - Will be taken from the WAN Settings
            Within the WAN Settings, find the link that is public wired and contains 'wan' in its name.
            Once the proper link is found, use that link's public ip as the NAT rule's Outside IP.

        3. Interface - Same as above.
            Once the proper link is found, use that link's interface as the NAT rule's Interface.

        4. Inside IP - Will be taken from the CPE's SSH port forwarding rule
            A SSH port forwarding rule should, by default, be in every Edge to get to the CPE behind it.
            By searching through the port forwarding rules and finding the rule that corresponds to the CPE,
            we can obtain the CPE's LAN IP.
            The corresponding rule will have a lAN IP property which we will use as the NAT rule's Inside IP

        5. Segment - NAT rule will be on the Voice segment
            The Voice Segment ID can be taken from the firewall, by looking through its segments and finding
            the Voice segment.
            Once found, Voice segment will contain its ID which is used to set the segment.

        If there are any missing properties, a print statement will be executed and return
        """

        # Set the NAT rule's name
        self.one_to_one_nat_rule_name = 'iTest 1 to 1 NAT'

        # Set the NAT rule's outside ip and interface
        """
        Look through the WAN Settings to find the link who has publicIpAddress as Edge's public ip.
        Once you find the correct WAN link, extract its interface and public ip
        """
        wan_links = self.get_wan_settings_links()
        for wan_link in wan_links:
            if wan_link['publicIpAddress'] == self.public_ip:
                self.one_to_one_nat_rule_outside_ip = wan_link['publicIpAddress']
                """
                Velocloud sets the links interfaces as a list. 
                For the most part, its a single item list though, so the first item in the list will be used.
                """
                self.one_to_one_nat_rule_interface = wan_link['interfaces'][0]
                break

        # Error check
        if not self.one_to_one_nat_rule_outside_ip or not self.one_to_one_nat_rule_interface:
            print(f'Error: No Public IP {self.public_ip} found within WAN Settings.')
            return

        # Set the NAT rule's inside ip
        """
        Obtain the NAT rule's Inside IP (aka CPE's LAN IP) by looking through the firewall rules and finding 
        a rule whose name contains the keyword 'itest' and 
        has WAN ports that matches self.ssh_port. If found, that rule will have the NAT rule's Inside IP 
        (aka CPE's LAN IP) in the rule's LAN IP field.
        """
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')
        for inbound_rule in firewall_module.data['inbound']:
            if 'itest' in inbound_rule['name'].lower() and inbound_rule['match']['dport_low'] == self.ssh_port and \
                    inbound_rule['match']['dport_high'] == self.ssh_port and \
                    inbound_rule['action']['nat']['lan_port'] == 22:
                self.one_to_one_nat_rule_inside_ip = inbound_rule['action']['nat']['lan_ip']
                break

        # Error check
        if not self.one_to_one_nat_rule_inside_ip:
            print('Traceback: No Inside IP found')
            return

        # Set the NAT rule's segment to voice segment
        # Obtain the Voice Segment
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name,
                                                              module=firewall_module)
        self.one_to_one_nat_rule_segment_id = firewall_voice_segment['segment']['segmentId']

        # Error check
        if not self.one_to_one_nat_rule_segment_id:
            print('Traceback: No Voice Segment ID found')
            return

    def is_one_to_one_nat_rule_present(self, print_statement: bool = True) -> bool:
        """
        Returns a bool and Prints a statement (optional, default True) verifying if our 'iTest 1 to 1 NAT' rule
        is present

        If there is a firewall rule that matches the properties set in set_one_to_one_nat_rule_properties()
            rule is present
        else
            rule is not present

        firewall_module:
            data:
                inbound:
                    LOOKING HERE IF THE 1 TO 1 NAT RULE IS PRESENT
        """

        # Get firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Search through the firewall inbound rules and check if there is a rule with all the properties set in
        # set_one_to_one_nat_rule_properties()
        for inbound_rule in firewall_module.data['inbound']:
            if inbound_rule['action']['type'] == 'one_to_one_nat' and \
                    inbound_rule['name'] == self.one_to_one_nat_rule_name and \
                    inbound_rule['match']['dip'] == self.one_to_one_nat_rule_outside_ip and \
                    inbound_rule['action']['interface'] == self.one_to_one_nat_rule_interface and \
                    inbound_rule['action']['nat']['lan_ip'] == self.one_to_one_nat_rule_inside_ip and \
                    inbound_rule['action']['segmentId'] == self.one_to_one_nat_rule_segment_id:
                if print_statement:
                    d = {'is_one_to_one_nat_rule_present': 'yes'}
                    print(d)
                return True

        if print_statement:
            d = {'is_one_to_one_nat_rule_present': 'no'}
            print(d)
        return False

    def add_one_to_one_nat_rule(self) -> None:
        """
        Adds a 1:1 NAT rule to the Edge's Firewall

        To add NAT rule we must first collect some properties.
        1. The NAT rule's name will be hardcoded to 'iTest 1 to 1 NAT'

        2. The NAT rule's outside ip will be taken from the WAN Settings
            Within the WAN Settings, find the link that is public and wired and contains 'wan' in its name.
            Once found, use that link's public ip for the NAT rule's outside ip

        3. The NAT rule's interface will be taken from the WAN Settings
            Within the WAN Settings, find the link that is public and wired and contains 'wan' in its name.
            Once found, use that link's interface for the NAT rule's interface.

        4. The NAT rule's inside (lan) ip will be taken from the Firewall
            Within the Firewall, find the port forwarding rule that contains 'itest' in its name, has wan ports
            that equal self.ssh_port, and has lan ports
            equal 22. Once found, use that rule's lan ip for the NAT rule's inside (lan) ip.

        5. The NAT rule's segment will be Voice segment
            The Voice Segment ID can be taken from the firewall, by looking through its segments and finding
            the Voice segment.
            Once found, Voice segment will contain its ID.
        """

        # Set up 1:1 NAT rule with the proper properties
        one_to_one_nat_rule = {
                                "name": self.one_to_one_nat_rule_name,
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
                                      "dip": self.one_to_one_nat_rule_outside_ip,
                                      "dport_low": -1,
                                      "dport_high": -1,
                                      "dsm": "any",
                                      "dvlan": -1,
                                      "proto": -1
                                },
                                "action": {
                                      "type": "one_to_one_nat",
                                      "segmentId": self.one_to_one_nat_rule_segment_id,
                                      "nat": {
                                            "lan_ip": self.one_to_one_nat_rule_inside_ip,
                                            "lan_port": -1,
                                            "outbound": False
                                      },
                                      "interface": self.one_to_one_nat_rule_interface,
                                      "subinterfaceId": -1
                                }
                              }

        # Get firewall module
        firewall_module = None
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Add rule to firewall module
        firewall_module.data['inbound'].append(one_to_one_nat_rule)

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id,
                                                       update=firewall_module)
        res = self.api.configurationUpdateConfigurationModule(param)
        print(res)

    def remove_one_to_one_nat_rule(self) -> None:
        """
        Removes the 1:1 NAT rule from the Edge's Firewall

        Will use the same logic as in is_one_to_one_nat_rule_present() to locate 1:1 NAT rule.
        Once found, it will remove the rule and push change
        """

        # Double check if rule even exists
        if not self.is_one_to_one_nat_rule_present(print_statement=False):
            return

        # Get Edge's firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Look through the firewall's inbound rules for the 1:1 nat rule, then remove it once found
        for inbound_rule in firewall_module.data['inbound']:
            if inbound_rule['action']['type'] == 'one_to_one_nat' and \
                    inbound_rule['name'] == self.one_to_one_nat_rule_name and \
                    inbound_rule['match']['dip'] == self.one_to_one_nat_rule_outside_ip and \
                    inbound_rule['action']['interface'] == self.one_to_one_nat_rule_interface and \
                    inbound_rule['action']['nat']['lan_ip'] == self.one_to_one_nat_rule_inside_ip and \
                    inbound_rule['action']['segmentId'] == self.one_to_one_nat_rule_segment_id:
                firewall_module.data['inbound'].remove(inbound_rule)
                break

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=self.enterprise_id,
                                                       update=firewall_module)
        res = self.api.configurationUpdateConfigurationModule(param)
        print(res)


# Globals
EDGE: FirewallOneToOneNatEdge


def set_globals(edge_id, enterprise_id, public_ip, ssh_port) -> None:
    global EDGE
    EDGE = FirewallOneToOneNatEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), public_ip=public_ip,
                                   ssh_port=int(ssh_port))


def is_one_to_one_nat_rule_present():
    EDGE.is_one_to_one_nat_rule_present()


def add_one_to_one_nat_rule():
    EDGE.add_one_to_one_nat_rule()


def remove_one_to_one_nat_rule():
    EDGE.remove_one_to_one_nat_rule()


def print_sdwan_public_wan_ip():
    print(EDGE.one_to_one_nat_rule_outside_ip)


if __name__ == '__main__':
    set_globals(edge_id=1, enterprise_id=1, ssh_port=2202, public_ip="216.241.61.7")