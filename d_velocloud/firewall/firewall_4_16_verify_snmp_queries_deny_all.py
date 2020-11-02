from my_velocloud.VelocloudEdge import VeloCloudEdge

"""
Test Case: Verify SNMP queries to the Edge, are denied if SNMP Access 'Deny All' is checked
Expected Results: All SNMP queries to the Edge be dropped
Usage: Confirm SNMP Settings v2c is enabled. Configure Edge's Firewall SNMP Access to 'Deny All'. Use snmpwalk to 
confirm SNMP queries are dropped. 

Details:
Ensure SNMP Settings v2c is enabled. You can find that in Edge's Device tab, scroll down to SNMP Settings. Port set to
161, community set to "tpc1n0c", and Allowed IPs: "Any" checked. 

Test by setting Edge's Firewall SNMP Access to "Deny All". Using another computer, execute a snmpwalk command 
and confirm you get a "No Response from [IP]" message. 
"""


DUT_EDGE: VeloCloudEdge


def set_snmp_access_to_deny_all() -> None:
    """
    Sets the Edge's Firewall SNMP Access to 'Deny All'

    SNMP Access can be found within the Edge's Firewall tab
    """

    # Get Edge's Edge Specific Firewall module
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    firewall_module['data']['services']['snmp']['enabled'] = False

    print(DUT_EDGE.update_configuration_module(module=firewall_module))


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, cpe_ssh_port=ssh_port)

    print(DUT_EDGE.set_snmp_v2c_settings())


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1, ssh_port=2201)
    set_snmp_access_to_deny_all()
