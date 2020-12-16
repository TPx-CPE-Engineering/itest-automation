from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge
import ipaddress

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
    Source      [VOICE VLAN NETWORK]                    [STATIC ROUTE SUBNET]    
    """

    # NAT RULE
    # Get the Network of Voice VLAN
    voice_vlan = DUT_EDGE.get_voice_segment_vlan()
    voice_vlan_ip = voice_vlan['cidrIp']  # Voice VLAN Network
    voice_vlan_netmask = voice_vlan['netmask']  # Voice VLAN Network
    voice_vlan_net = ipaddress.ip_network(voice_vlan_ip + '/' + voice_vlan_netmask, strict=False)
    inside_address = str(voice_vlan_net.network_address)

    inside_address_mask = 24
    outside_address = '172.16.223.21'
    outside_address_mask = 32

    nat_rule = {
        "insideCidrIp": inside_address,
        "insideCidrPrefix": inside_address_mask,
        "insidePort": -1,
        "outsideCidrIp": outside_address,
        "outsideCidrPrefix": outside_address_mask,
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
    create_edge(edge_id=245, enterprise_id=1, cpe_ssh_port=2202)
