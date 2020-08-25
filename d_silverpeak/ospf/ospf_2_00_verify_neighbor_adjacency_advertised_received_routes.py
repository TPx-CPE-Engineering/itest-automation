from my_silverpeak.OSPFEdge import OSPFEdge, Ixia, DEFAULT_OSPF_INFORMATION
import json
from ipaddress import ip_address
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_ospf_2_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

# VPorts
PORTS = [{'Name': 'Ethernet - 001',
          'Chassis IP': '10.255.224.70',
          'Card': 3,
          'Port': 3
          }]


# Object for SilverPeak
OSPF_EDGE: OSPFEdge

# Objects for Ixia IxNetwork
IXIA: Ixia


def start_ix_network():
    """
    Starts IxNetwork
    :return: None
    """
    global IXIA
    IXIA = Ixia()

    IXIA.start_ix_network(config=IX_NET_CONFIG_FILE,
                          vports=PORTS,
                          config_local=True)


def stop_ix_network(port_map_disconnect=True):
    """
    Stops IxNetwork
    :return: None
    """

    # Stop IxNetwork
    try:
        global IXIA
        IXIA.stop_ix_network(port_map_disconnect=port_map_disconnect)
    except NameError:
        IXIA = Ixia(clear_config=False)
        IXIA.stop_ix_network()


def get_ospf_neighbor_count():
    response = OSPF_EDGE.api.get_ospf_state_neighbors(applianceID=OSPF_EDGE.edge_id)

    neighbor_count = {
        'Neighbor Count': None
    }
    if response.data:
        neighbor_count['Neighbor Count'] = response.data['neighborCount']
        print(json.dumps(neighbor_count))
        print(json.dumps(response.data))
    else:
        neighbor_count['Neighbor Count'] = 0
        print(json.dumps(neighbor_count))


def get_edge_ospf_advertised_routes():
    # Getting all routes
    response = OSPF_EDGE.api.get_subnets(applianceID=OSPF_EDGE.edge_id)

    received_routes = []
    # Filter routes based based on default interface
    for entry in response.data['subnets']['entries']:
        if entry['state']['learned_ospf']:
            received_routes.append(entry['state']['prefix'])

    return received_routes


def get_ixia_ospf_advertised_routes():
    """
    Get Ixia's route ranges
    :return: list, Ixia's route ranges
    """

    # Get routes from Protocols -> OSPF -> [Configured Port] -> Route Ranges
    # ex. I have two route ranges.
    # For each route, get the 'First Route' and add the 'Number of Routes'.
    # This will create a list
    # ex. one of my routes ranges first route is: 172.16.55.0 and number of routes is: 3
    #   therefore, I will add 2 routes to my first route to create a total of 3 routes.
    #   my list would look like the following: [172.16.55.0, 172.16.55.1, 172.16.55.2]

    router = IXIA.IxNetwork.Vport.find().Protocols.find().Ospf.Router.find()
    route_ranges = router.RouteRange.find()
    route_ranges_ips = []
    for route in route_ranges:
        number_of_routes = route.NumberOfRoutes
        network_number = ip_address(address=route.NetworkNumber)
        mask = route.Mask
        metric = route.Metric
        while number_of_routes > 0:
            route_ranges_ips.append({'Network Number': str(network_number),
                                     'Mask': mask,
                                     'Metric': metric})
            network_number = network_number + 256
            number_of_routes -= 1

    return route_ranges_ips


def verify_if_edge_advertised_routes_match_ix_network():
    ixia_ad_routes = get_ixia_ospf_advertised_routes()
    edge_ad_routes = get_edge_ospf_advertised_routes()

    # Create a list of Ixia Advertised routes with their mask
    ixia_ad_routes_with_mask = []
    for route in ixia_ad_routes:
        route_with_mask = route['Network Number'] + '/' + str(route['Mask'])
        ixia_ad_routes_with_mask.append(route_with_mask)

    # If both lists match...
    if edge_ad_routes == ixia_ad_routes_with_mask:
        # Verification passed
        print({'match': 'yes'})
    else:
        # Verification failed
        print({'match': 'no'})
        print({'Edge': edge_ad_routes})
        print({'IxNetwork': ixia_ad_routes_with_mask})


def get_ixia_ospf_received_routes():
    # Refresh Learned Info
    interface = IXIA.IxNetwork.Vport.find().Protocols.find().Ospf.Router.find().Interface.find()
    interface.RefreshLearnedInfo()
    time.sleep(10)

    # Get the Learned LSA from Ixia
    learned_lsa = interface.LearnedLsa.find()
    learned_lsa_ips = []
    for lsa in learned_lsa:
        if lsa.LsaType == 'external':
            learned_lsa_ips.append(lsa.LinkStateId)

    return learned_lsa_ips


def get_edge_ospf_all_routes():
    # Getting all routes
    response = OSPF_EDGE.api.get_subnets(applianceID=OSPF_EDGE.edge_id)

    routes = []
    # Filter routes based based on default interface
    for entry in response.data['subnets']['entries']:
        routes.append(entry['state']['prefix'])

    return routes


def verify_if_edge_received_routes_match_ix_network():
    ixia_rec_routes = get_ixia_ospf_received_routes()

    # Since there isn't a clear way to obtain the specific received routes from Edge,
    # we will get all of them and verify if Ixia received routes are found.
    edge_all_routes = get_edge_ospf_all_routes()

    # Because Ixia does not provide mask will need to remove mask from Edge routes
    for n, route in enumerate(edge_all_routes):
        temp = route.split('/')
        edge_all_routes[n] = temp[0]

    # Verify if every ixia route is present in edge routes
    routes_not_found = []
    for route in ixia_rec_routes:
        if route not in edge_all_routes:
            routes_not_found.append(route)

    if len(routes_not_found) == 0:
        # Verification passed
        print({'match': 'yes'})
    else:
        # Verification failed
        print({'match': 'no'})
        print({'Ixia Routes not found in Edge': routes_not_found})


def create_edge(edge_id, enterprise_id=None):
    global OSPF_EDGE
    OSPF_EDGE = OSPFEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    OSPF_EDGE.enable_ospf()
    time.sleep(15)

    # Test requirements:
    #   Enable OSPF to OSPF Defaults

    OSPF_EDGE.set_ospf_settings_to_default()
    time.sleep(20)


if __name__ == '__main__':
    OSPF_EDGE = OSPFEdge(edge_id='18.NE', enterprise_id=None, ssh_port=None)
    get_ospf_neighbor_count()
