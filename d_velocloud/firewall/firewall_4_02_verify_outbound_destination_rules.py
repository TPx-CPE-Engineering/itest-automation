from velocloud.models import *
from my_velocloud.base_edge import BaseEdge


class Edge(BaseEdge):
    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)

    def get_edge_specific_firewall_voice_segment(self) -> dict:
        """
        Gets the Voice segment from the Edge's Edge Specific Firewall module

        Functions knows it has found the correct voice segment if it matches EDGE.voice_segment_name found in
        base_edge.py

        Edge's Edge Specific Firewall module json structure
        --------------------------------------------------
        Edge Specific Profile:
            DeviceSettings: ...
            Firewall:
                data:
                    segments:
                        LOOK HERE FOR VOICE SEGMENT AND RETURN THE SEGMENT THAT HAS A NAME EQUAL TO
                        EDGE.voice_segment_name
            WAN: ...
            QOS: ...
        Enterprise Profile: ...
        """

        # Get the Edge's Edge Specific Firewall module
        edges_firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Filter through the Firewalls segments and return the segment that has the same name as voice_segment_name
        for seg in edges_firewall.data['segments']:
            if seg['segment']['name'] == self.voice_segment_name:
                return seg

        print('No Voice segment found. Please verify if {} is the correct Voice segment\'s name. '
              'If not you can update within base_edge.py')
        return {}

    def is_firewall_outbound_rule_with_destination_ip_present(self, destination_ip: str) -> bool:
        """
        Function to check whether or not a firewall rule to block the destination ip is present on the Edge

        In order to say the rule is present, this functions looks for a rule with the following properties:
        1. rule's name is 'iTest Destination IP Block'
        2. rule's destination ip (dip) equals parameter destination_ip
        3. rule's action is 'deny'
        If a rule with all of the above conditions, then rule is present else it is not.
        """

        # Get Edge's Edge Specific Firewall module
        edges_firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get the Voice segment within the firewall
        edges_firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name,
                                                                    module=edges_firewall)

        # Searching for a rule with these properties...
        looking_for_rule = {'name': 'iTest Destination IP Block', 'dip': destination_ip, 'action': 'deny'}

        for rule in edges_firewall_voice_segment['outbound']:
            if rule['name'] == looking_for_rule['name'] and rule['match']['dip'] == looking_for_rule['dip'] and \
                    rule['action']['allow_or_deny'] == \
                    looking_for_rule['action']:
                d = {'is_firewall_outbound_rule_with_destination_ip_present': 'yes'}
                print(d)
                return True

        d = {'is_firewall_outbound_rule_with_destination_ip_present': 'no'}
        print(d)
        return False

    def add_firewall_outbound_rule_with_destination_ip(self, destination_ip: str) -> None:
        """
        Adds an outbound firewall rule to the Edge that blocks the given destination ip

        The rule will have the following properties:
        1. Rule's name will be 'iTest Destination IP Block'
        2. Rule's destination ip will be passed as a parameter
        3. Rule's action will be to 'deny' all traffic going to destination ip

        The API push response will be printed. Example of a good response: {error: None, rows: 1}
        """

        # Set properties for the rule that will be added
        rules_name = 'iTest Destination IP Block'
        rules_dip = destination_ip
        rules_action = 'deny'

        # Set up rule
        block_destination_ip_rule = {
                                    "name": rules_name,
                                    "match": {
                                        "appid": -1,
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
                                        "dip": rules_dip,
                                        "dport_low": -1,
                                        "dport_high": -1,
                                        "dsm": "255.255.255.255",
                                        "dvlan": -1,
                                        "proto": -1,
                                        "s_rule_type": "prefix",
                                        "d_rule_type": "prefix"
                                    },
                                    "action": {
                                        "allow_or_deny": rules_action
                                    },
                                    "loggingEnabled": False
                                    }

        # Get Edge's Edge Specific Firewall module
        edges_firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get the Voice segment from within the Firewall module
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name,
                                                              module=edges_firewall)

        # Append rule
        firewall_voice_segment['outbound'].append(block_destination_ip_rule)

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=edges_firewall.id, enterpriseId=self.enterprise_id,
                                                       update=edges_firewall)
        res = self.api.configurationUpdateConfigurationModule(param)
        print(res)

    def remove_firewall_outbound_rule_with_destination_ip(self, destination_ip: str) -> None:
        """
        Removes an outbound firewall rule from the Edge which blocks all traffic going to the destination ip

        Will identify which rule to removed if it has all the following properties:
        1. Rule's name equals 'iTest Destination IP Block'
        2. Rule's destination ip equals the parameter destination_ip
        3. Rule's action equals 'deny'

        The API push response will be printed. Example of a good response: {error: None, rows: 1}
        """

        # Set properties for the rule that will be added
        rules_name = 'iTest Destination IP Block'
        rules_dip = destination_ip
        rules_action = 'deny'

        # Get Edge's Edge Specific Firewall module
        edges_firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Get the Voice segment from within the Firewall module
        firewall_voice_segment = self.get_segment_from_module(segment_name=self.voice_segment_name,
                                                              module=edges_firewall)

        # Search for rule and remove
        for rule in firewall_voice_segment['outbound']:
            if rule['name'] == rules_name and rule['match']['dip'] == rules_dip and \
                    rule['action']['allow_or_deny'] == rules_action:
                firewall_voice_segment['outbound'].remove(rule)
                break

        # Push change
        param = ConfigurationUpdateConfigurationModule(id=edges_firewall.id, enterpriseId=self.enterprise_id,
                                                       update=edges_firewall)
        res = self.api.configurationUpdateConfigurationModule(param)
        print(res)


# Globals
EDGE: Edge


def set_globals(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = Edge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def is_firewall_outbound_rule_with_destination_ip_present(destination_ip: str):
    EDGE.is_firewall_outbound_rule_with_destination_ip_present(destination_ip=destination_ip)


def add_firewall_outbound_rule_with_destination_ip(destination_ip: str):
    EDGE.add_firewall_outbound_rule_with_destination_ip(destination_ip=destination_ip)


def remove_firewall_outbound_rule_with_destination_ip(destination_ip: str):
    EDGE.remove_firewall_outbound_rule_with_destination_ip(destination_ip=destination_ip)
