from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge

"""
LAN-Side NAT Verify Destination NAT Route Matching

Usage:
a.	Configure a Destination LAN-side NAT at site 1: inside 172.16.100.100/32, outside 192.168.100.100/32, 
source route [CPE_IP].
b.	Advertise VLAN 1 at site 1.
c.	Verify that host 1 can ping host 2 at 172.16.100.100.
d.	Modify the LAN-side NAT source route to be 172.31.0.11/32.
e.	Verify that host 1 can no longer ping host 2 at 172.16.100.100

Expected Results:
Before step (d) verify host 1 can ping host 2 at 172.16.100.100
After step (d) verify host 1 can no longer ping host 2 at 172.16.100.100
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
    Add LAN-Side NAT Rule with CPE IP as Source Route

    NAT Source or Destination
    Type            Inside Addr         Outside Addr            Source Route
    Destination     172.16.100.100/32   192.168.100.100/32      [CPE IP]/32

    :return: None
    """

    cpe_ip = DUT_EDGE.get_cpe_lan_ip()

    # NAT RULE
    nat_rule = {
        "insideCidrIp": "172.16.100.100",
        "insideCidrPrefix": 32,
        "insidePort": -1,
        "outsideCidrIp": '192.168.100.100',
        "outsideCidrPrefix": 32,
        "outsidePort": -1,
        "type": "destination",
        "description": "Added by iTest",
        "srcCidrIp": cpe_ip,
        "srcCidrPrefix": 32,
        "destCidrIp": "",
        "destCidrPrefix": -1,
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.255",
        "srcNetmask": "255.255.255.255",
        "destNetmask": ""
    }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def add_random_ip_lan_side_nat_rule():
    """
    Add LAN-Side NAT Rule

    NAT Source or Destination
    Type            Inside Addr         Outside Addr            Source Route
    Destination     172.16.100.100/32   192.168.100.100/32      172.31.0.11/32

    :return: None
    """

    # NAT RULE
    nat_rule = {
        "insideCidrIp": "172.16.100.100",
        "insideCidrPrefix": 32,
        "insidePort": -1,
        "outsideCidrIp": '192.168.100.100',
        "outsideCidrPrefix": 32,
        "outsidePort": -1,
        "type": "destination",
        "description": "Added by iTest",
        "srcCidrIp": '172.31.0.11',
        "srcCidrPrefix": 32,
        "destCidrIp": "",
        "destCidrPrefix": -1,
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.255",
        "srcNetmask": "255.255.255.255",
        "destNetmask": ""
    }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def delete_all_nat_rules_from_segment(segment_name='Voice'):
    print("Deleting all LAN-NAT Rules in Voice Segment...")
    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name=segment_name))


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
    create_edge(edge_id=249, enterprise_id=1, cpe_ssh_port=2202)
