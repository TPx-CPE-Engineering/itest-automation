from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge

"""
Verify simultaneous source & destination NAT

Usage:
a.	Configure a Source & Destination LAN-side NAT at site 1: source mapping is CPE IP/32 -> 172.16.223.21/32; 
destination mapping is 172.16.100.100/32 -> Ubuntu VM/32.
b.	Do not advertise VLAN 1 at site 1.
c.	Verify that host 1 (CPE) can ping host 2 (Ubuntu VM) with the NAT IP 172.16.100.100
d.	Verify that host 2 (Ubuntu VM) can ping host 1 (CPE) with the NAT IP 172.16.223.21

Expected Results:
Host 1 (CPE) able to ping Host 2 (Ubuntu VM) with NAT IP 172.16.100.100
Host 2 (Ubuntu VM) able to ping Host 1 (CPE) with NAT IP 172.16.223.21
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


def add_lan_side_nat_rule():
    """
    Adds DUAL LAN-Side NAT Rule with CPE IP as Inside Address
    :return: None
    """

    """
    Adding LAN-Side NAT Rule 
    
    NAT Source and Destination
    Type    Inside Addr     Outside Addr    Type        Inside Addr     Outside Addr
    Source  [CPE IP Addr]   172.16.223.21   Destination 172.16.100.100  192.168.100.100
    """

    cpe_ip = DUT_EDGE.get_cpe_lan_ip()

    # DUAL NAT RULE
    dual_nat_rule = {
          "srcInsideCidrIp": cpe_ip,
          "srcOutsideCidrIp": "172.16.223.21",
          "destInsideCidrIp": "172.16.100.100",
          "destOutsideCidrIp": "192.168.100.100",
          "srcInsideCidrPrefix": 32,
          "srcOutsideCidrPrefix": 32,
          "destInsideCidrPrefix": 32,
          "destOutsideCidrPrefix": 32,
          "description": "Added by iTest",
          "srcInsideNetmask": "255.255.255.255",
          "srcOutsideNetmask": "255.255.255.255",
          "destInsideNetmask": "255.255.255.255",
          "destOutsideNetmask": "255.255.255.255"
        }

    print("Adding LAN-Side NAT Rules on Voice Segment...")
    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[], dual_rules=[dual_nat_rule]))


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
