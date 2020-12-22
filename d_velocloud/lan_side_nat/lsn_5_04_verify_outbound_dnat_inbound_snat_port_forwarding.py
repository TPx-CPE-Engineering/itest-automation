from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge

"""
Verify Outbound DNAT / Inbound SNAT with port forwarding

Usage:
a.	Use the configuration from test case 4 but configure 2201 as the inside port and 22 as the outside port in the LAN-side NAT.
b.	Advertise VLAN 1 at site 1.
c.	Verify that host 1 cannot ping 172.16.223.21
d.	Verify that host 1 can SSH to 172.16.223.21 on port 2201.

Expected Results:
Host 1 unable to ping 172.16.223.21
Host 1 able to SSH to 172.16.223.21:2201
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
    Destination 172.16.223.21           2201            192.168.100.100         22
    """

    # NAT RULE
    nat_rule = {
        "insideCidrIp": '172.16.223.21',
        "insideCidrPrefix": 32,
        "insidePort": 2201,
        "outsideCidrIp": '192.168.100.100',
        "outsideCidrPrefix": 32,
        "outsidePort": 22,
        "type": "destination",
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
