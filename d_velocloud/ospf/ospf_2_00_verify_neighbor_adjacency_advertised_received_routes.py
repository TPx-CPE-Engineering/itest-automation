from my_velocloud.VelocloudEdge import OSPFVeloCloudEdge
from d_ixia.ix_network.Ix_Network import IxNetwork
from ipaddress import ip_address
import time
import json

DUT_EDGE: OSPFVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ix_network():
    ix_network_config = 'VC_ospf_2_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

    corporate_vlan = DUT_EDGE.get_vlan(vlan_id=1)

    # Get IP Address of VLAN
    # This will be Ix Network Interface Gateway
    corporate_vlan_ip_address = corporate_vlan['cidrIp']

    # Set Ix Network IP
    # It will be Ix Network Gateway plus 1
    ip = ip_address(address=corporate_vlan_ip_address)
    ip = ip + 1

    IX_NETWORK.start_ospf(config=ix_network_config,
                          config_local=True,
                          ipv4_address=str(ip),
                          ipv4_mask_width='24',
                          ipv4_gateway=corporate_vlan_ip_address)


def stop_ix_network():
    IX_NETWORK.stop_ix_network()

    restore_settings()


def restore_settings():
    file = 'C:/Users/dataeng/PycharmProjects/iTest_Automation/d_velocloud/ospf/ospf_device_settings.json'
    print(DUT_EDGE.restore_config_from_filename(filename=file))
    DUT_EDGE.delete_filename(filename=file)


def verify_if_advertised_routes_match():

    # Get Edges OSPF Routes
    edge_routes = get_advertised_routes()

    # Get Edges Router ID
    # Edges Router ID will be VLAN 1 IP Address plus 1
    corporate_vlan = DUT_EDGE.get_vlan(vlan_id=1)

    edge_router_id = str(ip_address(corporate_vlan['cidrIp']) + 1)

    # Get all Edges OSPF routes and extract the routes with matching Edge Router Id
    edges_routes_with_id = []
    for route in edge_routes:
        if route['ADV Router'] == edge_router_id:
            edges_routes_with_id.append({route['Link ID']: route['ADV Router']})

    # Now get Ix Networks information
    # Get the Router Id from IxNetwork
    # Protocols -> OSPF -> "DUT Edge" -> "RID - 192.168.184.2" -> Router ID
    router = IX_NETWORK.IxNetwork.Vport.find().Protocols.find().Ospf.Router.find()
    router_id = router.RouterId

    # Get Route Ranges from IxNetwork
    # Protocols -> OSPF -> "DUT Edge" -> "RID - 192.168.184.2" -> RouteRanges
    route_ranges = router.RouteRange.find()

    # Grab each first route in route ranges and add routes based on the number of routes.
    # ex.   first route = '172.17.55.0' and number of routes 2
    #       second route = '172.17.56.0'
    # Will create a list of dict with the router_id being the value
    # ex.   [{172.17.55.0: 192.168.184.2}
    #           ...
    #            ...
    #       ]
    # These values come from IxNetwork
    route_ranges_ips = []
    for route in route_ranges:
        number_of_routes = route.NumberOfRoutes
        ip = ip_address(address=route.NetworkNumber)
        while number_of_routes > 0:
            route_ranges_ips.append({str(ip): router_id})
            ip = ip + 256
            number_of_routes -= 1

    # Verify if the list created from Velo and list created from IxNetwork match
    if route_ranges_ips == edges_routes_with_id:
        match = True
    else:
        match = False

    response = {
        'match': match,
        'Velo': edges_routes_with_id,
        'IxNetwork': route_ranges_ips
    }

    print(json.dumps(response))


def get_advertised_routes():
    response = DUT_EDGE.get_ospf_database()
    response_lines = response.splitlines()

    # Find header start
    header_start = 0
    for item in range(0, len(response_lines)):
        if 'Link ID' in response_lines[item] and 'ADV' in response_lines[item] and 'Router' in response_lines[item]:
            header_start = item

    routes = []
    # Get all entries after the table header
    for line in response_lines[header_start + 1:]:
        line_split = line.split()
        if len(line_split) == 8:
            entry = {
                'Link ID': line_split[0],
                'ADV Router': line_split[1],
                'Age': line_split[2],
                'Sequence Num': line_split[3],
                'CkSum': line_split[4],
                'Route': f"{line_split[5]} {line_split[6]} {line_split[7]}"
            }
            routes.append(entry)

    return routes


def get_ospf_neighbors_count():
    ospf_neighbors = DUT_EDGE.get_ospf_neighbors()
    print(len(ospf_neighbors))


def verify_if_received_routes_match():
    # Get Edges OSPF Routes
    edge_routes = get_advertised_routes()

    # Get Edges Router ID
    # Edges Router ID will be VLAN 1 IP Address plus 1
    corporate_vlan = DUT_EDGE.get_vlan(vlan_id=1)
    edge_router_id = str(ip_address(corporate_vlan['cidrIp']) + 1)

    # Get all Edges OSPF routes and extract the routes that do not match Edge Router Id
    edges_routes_with_id = []
    for route in edge_routes:
        if not route['ADV Router'] == edge_router_id:
            edges_routes_with_id.append({route['Link ID']: route['ADV Router']})

    # Now get Ix Networks information
    ospf_interface = IX_NETWORK.IxNetwork.Vport.find().Protocols.find().Ospf.Router.find().Interface.find()
    ospf_interface.RefreshLearnedInfo()
    time.sleep(10)

    learned_lsa = ospf_interface.LearnedLsa.find()
    learned_lsa_ips = []
    for lsa in learned_lsa:
        if lsa.LsaType == 'external':
            learned_lsa_ips.append({lsa.LinkStateId: lsa.AdvRouterId})

    if learned_lsa_ips == edges_routes_with_id:
        match = True
    else:
        match = False

    response = {
        'match': match,
        'Velo': edges_routes_with_id,
        'IxNetwork': learned_lsa_ips
    }

    print(json.dumps(response))


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = OSPFVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # Save settings before modifying in order to reformat Edge
    DUT_EDGE.save_module_to_restore(module_name='deviceSettings', path='C:/Users/dataeng/PycharmProjects/iTest_Automation/d_velocloud/ospf/',
                                    filename='ospf_device_settings')

    # Steps to configure edge for OSPF
    # Find a Interface that is in the Global Segment Interfaces, in this case it'll be 'GE2'
    interface_config = DUT_EDGE.get_ospf_interface_config()
    print('Adding \'{}\' as a static interface with IP Address \'{}\' for OSPF testing...'.format(
        interface_config['name'], interface_config['addressing']['cidrIp']
    ))

    # Add Interface Config to Edge
    print(DUT_EDGE.add_routed_interface(interface=interface_config, vlan_id=1))

    # Initiate Ix Network
    IX_NETWORK = IxNetwork(clear_config=True)


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    verify_if_received_routes_match()
