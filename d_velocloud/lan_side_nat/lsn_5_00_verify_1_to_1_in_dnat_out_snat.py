from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge, Globals
# from networking_scripts.my_ssh import ssh_connect

DUT_EDGE: LANSideNatVelocloudEdge

STATIC_ROUTE_SUBNET = '172.16.223.0'
STATIC_ROUTE_SUBNET_MASK = '24'


def add_static_route():
    """
    Adds a static route to voice segment
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

    print(DUT_EDGE.add_static_route_rule_to_segment(segment_name=Globals.VOICE_SEGMENT_NAME, rule=static_route_rule))


def add_lan_side_nat_rule():
    """
    Add LAN-Side NAT Rule
    :return: nONE
    """

    inside_address = DUT_EDGE.get_cpe_lan_ip()
    inside_address_mask = 32

    outside_address = '172.16.223.20'
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
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.0",
        "srcNetmask": "",
        "destNetmask": ""
    }

    print(DUT_EDGE.add_nat_rules_to_segment(segment_name=Globals.VOICE_SEGMENT_NAME, rules=[nat_rule], dual_rules=[]))


def create_edge(edge_id, enterprise_id, cpe_ssh_port):
    global DUT_EDGE
    DUT_EDGE = LANSideNatVelocloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, cpe_ssh_port=cpe_ssh_port)

    print(DUT_EDGE.set_advertise_on_vlan(advertise_enabled=False, vlan_name=Globals.VOICE_SEGMENT_NAME))
    add_static_route()


def restore_configuration():
    print(DUT_EDGE.set_advertise_on_vlan(advertise_enabled=True, vlan_name=Globals.VOICE_SEGMENT_NAME))
    print(DUT_EDGE.delete_all_static_routes_from_segment(segment_name=Globals.VOICE_SEGMENT_NAME))

    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name=Globals.VOICE_SEGMENT_NAME))


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1, cpe_ssh_port=2202)
    # ssh_client = ssh_connect(host='10.255.20.159', port=22, username='cpeeng', password='Fan-Brain-K')
    # stdin, stdout, stderr = ssh_client.exec_command(command='ping -c 5 8.8.8.8')
    # print(stdout.read().decode('ascii'))
