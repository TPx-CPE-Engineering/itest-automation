from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge

"""
Verify Source NAT route matching

Usage:
a.	Configure a Source LAN-side NAT at site 1: inside [CPE IP]/32, outside 172.16.223.21/32, 
destination route 192.168.100.100/32.
b.	Do not advertise VLAN 1 at site 1.
c.	Verify that host 1 can ping host 2 at 192.168.100.100.
d.	Modify the LAN-side NAT destination route to be 172.31.0.11/32.
e.	Verify that host 1 can no longer ping host 2 at 192.168.100.100.

Expected Results:
Before step (d) verify host 1 is able to ping host 2 at 192.168.100.100
After step (d) verify  host 1 is no longer able to ping host 2 at 192.168.100.100
"""

DUT_EDGE: LANSideNatVelocloudEdge

STATIC_ROUTE_SUBNET = '172.16.223.0'
STATIC_ROUTE_SUBNET_MASK = '24'


def add_static_route():
    """
    Adds a static route to voice segment

    Static Route Settings
    Subnet                  Source IP   Next Hop                   Interface           VLAN    Cost Preferred  Advertise
    [STATIC_ROUTE_SUBNET]   n/a         [VOICE VLAN IP ADDRESS]    [not applicable]    none    0    true       true

    :return: None
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


def add_cpe_ip_lan_side_nat_rule():
    """
    Add LAN-Side NAT Rule with CPE IP as Inside Addr

    NAT Source or Destination
    Type          Inside Addr       Outside Addr           Destination Route
    Source        [CPE IP]/32       172.16.223.21/32       192.168.100.100/32

    :return: None
    """

    cpe_ip = DUT_EDGE.get_cpe_lan_ip()

    # NAT RULE
    nat_rule = {
        "insideCidrIp": cpe_ip,
        "insideCidrPrefix": 32,
        "insidePort": -1,
        "outsideCidrIp": '172.16.223.21',
        "outsideCidrPrefix": 32,
        "outsidePort": -1,
        "type": "source",
        "description": "Added by iTest",
        "srcCidrIp": "",
        "srcCidrPrefix": "",
        "destCidrIp": "192.168.100.100",
        "destCidrPrefix": 32,
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.255",
        "srcNetmask": "",
        "destNetmask": "255.255.255.255"
    }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def add_random_ip_lan_side_nat_rule():
    """
    Add LAN-Side NAT Rule

    NAT Source or Destination
    Type          Inside Addr       Outside Addr           Destination Route
    Source        172.31.0.11/32    172.16.223.21/32       192.168.100.100/32

    :return: None
    """

    # NAT RULE
    nat_rule = {
        "insideCidrIp": "172.31.0.11",
        "insideCidrPrefix": 32,
        "insidePort": -1,
        "outsideCidrIp": '172.16.223.21',
        "outsideCidrPrefix": 32,
        "outsidePort": -1,
        "type": "source",
        "description": "Added by iTest",
        "srcCidrIp": "",
        "srcCidrPrefix": "",
        "destCidrIp": "192.168.100.100",
        "destCidrPrefix": 32,
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.255",
        "srcNetmask": "",
        "destNetmask": "255.255.255.255"
    }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def delete_all_nat_rules_from_segment(segment_name='Voice'):
    print("Deleting all LAN-NAT Rules in Voice Segment...")
    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name=segment_name))


def create_edge(edge_id, enterprise_id, cpe_ssh_port):
    global DUT_EDGE
    DUT_EDGE = LANSideNatVelocloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, cpe_ssh_port=cpe_ssh_port)

    print("Setting Voice VLAN Advertise Enabled to False...")
    print(DUT_EDGE.set_advertise_on_vlan(advertise_enabled=False, vlan_name='Voice'))

    add_static_route()


def restore_configuration():
    print("Setting Voice VLAN Advertise Enabled to True...")
    print(DUT_EDGE.set_advertise_on_vlan(advertise_enabled=True, vlan_name='Voice'))

    print("Deleting all Static Routes in Voice Segment...")
    print(DUT_EDGE.delete_all_static_routes_from_segment(segment_name='Voice'))

    print("Deleting all LAN-NAT Rules in Voice Segment...")
    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name='Voice'))


if __name__ == '__main__':
    create_edge(edge_id=249, enterprise_id=1, cpe_ssh_port=2202)
