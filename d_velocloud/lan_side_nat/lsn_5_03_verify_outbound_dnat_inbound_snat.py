from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge
import ipaddress

"""
Verify Outbound DNAT / Inbound SNAT

Usage:
a.	Configure a Destination LAN-side NAT at site 1: inside 172.16.238.155/32, outside 192.168.138.155/32
b.	Advertise VLAN 1 at site 1.
c.	Verify that host 1 can ping 172.16.238.155.

Expected Results:
Host 1 is able to ping 172.16.238.155
"""

DUT_EDGE: LANSideNatVelocloudEdge

STATIC_ROUTE_SUBNET = '172.16.223.0'
STATIC_ROUTE_SUBNET_MASK = '24'


def add_static_route():
    """
    Adds a static route to voice segment
    :return: None
    """

    """
    Adding 1 Static Route Rule

    Subnet                  Source IP   Next Hop                   Interface           VLAN    Cost Preferred  Advertise
    [STATIC ROUTE SUBNET]   n/a         [VOICE VLAN IP ADDRESS]    [not applicable]    none    0    true       true
    """

    voice_vlan = DUT_EDGE.get_voice_segment_vlan()
    voice_vlan_ip_address = voice_vlan['cidrIp']

    static_route_rule = {
        "destination": STATIC_ROUTE_SUBNET,
        "netmask": "255.255.255.0",
        "sourceIp": None,
        "gateway": voice_vlan_ip_address,
        "cost": 0,
        "preferred": True,
        "description": "Added by iTest",
        "cidrPrefix": STATIC_ROUTE_SUBNET_MASK,
        "wanInterface": "",
        "subinterfaceId": -1,
        "icmpProbeLogicalId": None,
        "vlanId": None,
        "advertise": True
    }

    print("Adding a Static Route on Voice Segment...")
    print(DUT_EDGE.add_static_route_rule_to_segment(segment_name='Voice', rule=static_route_rule))


def add_lan_side_nat_rule():
    """
    Add LAN-Side NAT Rule
    :return: None
    """

    """
    Adding LAN-Side NAT Rule

    Type        Inside Address          Inside Port     Outside Address         Outside Port
    Destination [VOICE VLAN NETWORK]                    [STATIC ROUTE SUBNET]    
    """

    # NAT RULE
    nat_rule = {
        "insideCidrIp": '1.1.1.1',
        "insideCidrPrefix": 24,
        "insidePort": -1,
        "outsideCidrIp": '1.1.1.1',
        "outsideCidrPrefix": 24,
        "outsidePort": -1,
        "type": "source",
        "description": "Added by iTest",
        "srcCidrIp": "",
        "srcCidrPrefix": "",
        "destCidrIp": "",
        "destCidrPrefix": "",
        "insideNetmask": "255.255.255.0",
        "outsideNetmask": "255.255.255.255",
        "srcNetmask": "",
        "destNetmask": ""
    }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def create_edge(edge_id, enterprise_id, cpe_ssh_port):
    global DUT_EDGE
    DUT_EDGE = LANSideNatVelocloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, cpe_ssh_port=cpe_ssh_port)

    add_static_route()


def restore_configuration():
    print("Deleting all Static Routes in Voice Segment...")
    print(DUT_EDGE.delete_all_static_routes_from_segment(segment_name='Voice'))

    print("Deleting all LAN-NAT Rules in Voice Segment...")
    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name='Voice'))


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1, cpe_ssh_port=2202)
