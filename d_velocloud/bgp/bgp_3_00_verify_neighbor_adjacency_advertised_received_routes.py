from my_velocloud.VelocloudEdge import BGPVeloCloudEdge
from ix_network.Ix_Network import IxNetwork
import time
from ipaddress import ip_address

DUT_EDGE: BGPVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ix_network():
    ix_network_config = 'VC_bgp_3_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

    # IX Network IPV4 should be of neighbor
    ipv4_address = DUT_EDGE.get_new_bgp_neighbor_ip()

    # IX Network IPV4 Gateway should be of the VLAN on Global Segment
    ipv4_gateway = DUT_EDGE.get_vlan_ip_address_from_segment(segment_name='Global Segment')

    IX_NETWORK.start_bgp_ix_network(config=ix_network_config,
                                    config_local=True,
                                    ipv4_address=ipv4_address,
                                    ipv4_mask_width='24',
                                    ipv4_gateway=ipv4_gateway)


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = BGPVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # For this test ...
    # Set Neighbors
    new_neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    new_neighbor_asn = '65535'
    print(f"Overwriting BGP neighbors and adding new neighbor \'{new_neighbor_ip}\' with ASN \'{new_neighbor_asn}\'.")
    DUT_EDGE.overwrite_bgp_neighbors(neighbor_ip=new_neighbor_ip, neighbor_asn=new_neighbor_asn)

    # Initiate Ix Network
    IX_NETWORK = IxNetwork(clear_config=False)


def get_bgp_summary():
    print(DUT_EDGE.get_bgp_summary())


def get_bgp_neighbor_advertised_routes():
    segment_id = DUT_EDGE.default_bgp_segment['segment']['segmentId']
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    print(DUT_EDGE.get_bgp_neighbor_advertised_routes(segment_id=segment_id,
                                                      neighbor_ip=neighbor_ip))


def get_bgp_neighbor_received_routes():
    segment_id = DUT_EDGE.default_bgp_segment['segment']['segmentId']
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    print(DUT_EDGE.get_bgp_neighbor_received_routes(segment_id=segment_id,
                                                    neighbor_ip=neighbor_ip))


def get_advertised_routes() -> []:
    """
    Get Edges Advertised Routes
    :return:
    """
    segment_id = DUT_EDGE.default_bgp_segment['segment']['segmentId']
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    response = DUT_EDGE.get_bgp_neighbor_advertised_routes(segment_id=segment_id, neighbor_ip=neighbor_ip)

    response_lines = response.splitlines()
    header_start = 0
    for item in range(0, len(response_lines)):
        # Find Header
        if 'Network' in response_lines[item] and 'Next Hop' in response_lines[item] and 'Metric' in response_lines[item]:
            header_start = item

    bgp_advertised_routes = []
    # Get all the bgp entries after the table header
    for line in response_lines[header_start + 1:]:
        line_split = line.split()

        if len(line_split) == 7:
            bgp_entry = {
                'Status Code': line_split[0],
                'Network': line_split[1],
                'Next Hop': line_split[2],
                'Metric': line_split[3],
                'LocPrf': line_split[4],
                'Weight': line_split[5],
                'Path': line_split[6]
            }
            bgp_advertised_routes.append(bgp_entry)

    return bgp_advertised_routes


def do_advertise_routes_match():
    """
    Prints yes or no if IxNetwork IPv4 Unicast Routes IP's match with Velo BGP Neighbor Advertised Routes IPs
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_advertise_routes = get_advertised_routes()
    edge_advertise_routes_ips = []
    for route in edge_advertise_routes:
        edge_advertise_routes_ips.append(route['Network'].split('/')[0])

    # Get Neighbor Range
    neighbor_range = IX_NETWORK.IxNetwork.Vport.find().Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()
    time.sleep(10)

    ipv4_unicast = neighbor_range.find().LearnedInformation.Ipv4Unicast.find()

    # Create list of ips taken from Protocol -> BGP
    # -> DUT Port -> IPv4 Peers -> 'Internal - 192.168.144.2-1' -> Learned Routes
    ix_network_advertise_routes_ips = []
    for ip in ipv4_unicast:
        ix_network_advertise_routes_ips.append(ip.IpPrefix)

    # Check if the ips match, expecting to match to pass the test
    if edge_advertise_routes_ips == ix_network_advertise_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Advertise Routes IPs': edge_advertise_routes_ips})
    print({'IxNetwork Advertise Routes IPs': ix_network_advertise_routes_ips})


def get_learned_routes() -> []:
    """
    Get Edges Learned Routes
    :return:
    """
    segment_id = DUT_EDGE.default_bgp_segment['segment']['segmentId']
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    response = DUT_EDGE.get_bgp_neighbor_received_routes(segment_id=segment_id, neighbor_ip=neighbor_ip)

    response_lines = response.splitlines()

    # Find header start
    header_start = 0
    for item in range(0, len(response_lines)):
        if 'Network' in response_lines[item] and 'Next Hop' in response_lines[item] and 'Metric' in response_lines[item]:
            header_start = item

    bgp_learned_routes = []
    # Get all the bgp entries after the table header
    for line in response_lines[header_start + 1:]:
        line_split = line.split()
        if len(line_split) == 6:
            bgp_entry = {
                'Status Code': line_split[0],
                'Network': line_split[1],
                'Next Hop': line_split[2],
                'LocPrf': line_split[3],
                'Weight': line_split[4],
                'Path': line_split[5]
            }
            bgp_learned_routes.append(bgp_entry)

    return bgp_learned_routes


def do_received_routes_match():
    """
    Prints yes or no if IxNetwork Route Range IPs match with Velo BGP Recieved Routes IPs
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_received_routes = get_learned_routes()
    edge_received_routes_ips = [route['Network'].split('/')[0] for route in edge_received_routes]

    neighbor_range = IX_NETWORK.IxNetwork.Vport.find().Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()

    route_ranges = neighbor_range.RouteRange.find()

    # Gather Ix Network Routes IPs
    ix_network_received_routes_ips = []
    for route in route_ranges:
        number_of_routes = route.NumRoutes
        ip = ip_address(address=route.NetworkAddress)
        while number_of_routes > 0:
            ix_network_received_routes_ips.append(str(ip))
            # Increase IP by 256
            ip = ip + 256
            number_of_routes -= 1

    if edge_received_routes_ips == ix_network_received_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Received Routes IPs': edge_received_routes_ips})
    print({'IxNetwork Received Routes IPs': ix_network_received_routes_ips})


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    do_received_routes_match()
