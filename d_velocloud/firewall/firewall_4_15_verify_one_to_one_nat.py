# from velocloud.models import *
# from my_velocloud.BaseEdge import BaseEdge
from my_velocloud.VelocloudEdge import VeloCloudEdge

"""
Test Case: Verify 1:1 NAT
Expected Results: Verify CPE replies to a snmpwalk request when 1:1 NAT rule is enabled on the SD-WAN
Usage: Enable 1:1 NAT rule for CPE on SD-WAN, execute a snmpwalk request to the SD-WAN's public WAN IP, and 
verify CPE replies.
"""


# Globals
DUT_EDGE: VeloCloudEdge
PUBLIC_IP: str


def create_edge(edge_id, enterprise_id, public_ip, ssh_port) -> None:
    global DUT_EDGE, PUBLIC_IP

    PUBLIC_IP = public_ip
    DUT_EDGE = VeloCloudEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), cpe_ssh_port=int(ssh_port))


def get_nat_properties_from_port_forwarding_rules():
    """
    :return:
    """

    """
    Since Port Forwarding rule is always assumed to be there, we can use its properties to fulfill 1 to 1 NAT rules
    """

    firewall = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    for rule in firewall['data']['inbound']:
        if rule['match']['dport_low'] == DUT_EDGE.cpe_ssh_port and rule['match']['dport_high'] == DUT_EDGE.cpe_ssh_port:
            return {'segment id': rule['action']['segmentId'],
                    'interface': rule['action']['interface'],
                    'lan ip': rule['action']['nat']['lan_ip']}


def add_one_to_one_nat_rule():
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

    one_to_one_properties = get_nat_properties_from_port_forwarding_rules()

    # Set up 1:1 NAT rule with the proper properties
    one_to_one_nat_rule = {
        "name": 'iTest 1 to 1 NAT',
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
            "dip": PUBLIC_IP,
            "dport_low": -1,
            "dport_high": -1,
            "dsm": "any",
            "dvlan": -1,
            "proto": -1
        },
        "action": {
            "type": "one_to_one_nat",
            "segmentId": one_to_one_properties['segment id'],
            "nat": {
                "lan_ip": one_to_one_properties['lan ip'],
                "lan_port": -1,
                "outbound": True
            },
            "interface": one_to_one_properties['interface'],
            "subinterfaceId": -1
        }
    }

    # Get firewall module
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    firewall_module['data']['inbound'].append(one_to_one_nat_rule)

    print(DUT_EDGE.update_configuration_module(module=firewall_module))


def remove_one_to_one_nat_rule():
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    for rule in firewall_module['data']['inbound']:
        if rule['name'] == 'iTest 1 to 1 NAT':
            firewall_module['data']['inbound'].remove(rule)

    # Push change
    print(DUT_EDGE.update_configuration_module(module=firewall_module))


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1, ssh_port=2202, public_ip="66.17.13.160")
    remove_one_to_one_nat_rule()