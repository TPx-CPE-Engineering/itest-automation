from my_velocloud.VelocloudEdge import BGPVeloCloudEdge
from ix_network.Ix_Network import IxNetwork

DUT_EDGE: BGPVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ixia():
    ix_network_config = 'VC_bgp_3_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

    # IX Network IPV4 should be of neighbor
    ipv4_address = DUT_EDGE.get_new_bgp_neighbor_ip()

    # IX Network IPV4 Gateway should be of the VLAN on Global Segment
    ipv4_gateway = DUT_EDGE.get_vlan_ip_address_from_segment(segment_name='Global Segment')

    IX_NETWORK.start_bgp_ix_network(config=ix_network_config,
                                    config_local=False,
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
    IX_NETWORK = IxNetwork()


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


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    # start_ixia()
    get_bgp_neighbor_received_routes()
