from my_velocloud.VelocloudEdge import BGPVeloCloudEdge
from ix_network.Ix_Network import IxNetwork

DUT_EDGE: BGPVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ix_network(enable_md5=False, md5_password=None):
    ix_network_config = 'VC_bgp_3_01_verify_md5_authentication.ixncfg'

    # IX Network IPV4 should be of neighbor
    ipv4_address = DUT_EDGE.get_new_bgp_neighbor_ip()

    # IX Network IPV4 Gateway should be of the VLAN on Global Segment
    ipv4_gateway = DUT_EDGE.get_vlan_ip_address_from_segment(segment_name='Global Segment')

    IX_NETWORK.start_bgp_ix_network(config=ix_network_config,
                                    config_local=True,
                                    ipv4_address=ipv4_address,
                                    ipv4_mask_width='24',
                                    ipv4_gateway=ipv4_gateway,
                                    enable_md5=enable_md5,
                                    md5_password=md5_password)


def stop_ix_network():
    IX_NETWORK.stop_ix_network()


def restore_bgp_default_settings():
    print('')


def disable_bgp():
    DUT_EDGE.disable_bgp_edge_override_on_edge_segment()


def enable_bgp_md5_auth(password='testing123'):
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    print(DUT_EDGE.enable_md5_on_bgp_neighbor(neighbor_ip=neighbor_ip, md5_password=password))


def disable_bgp_md5_auth():
    neighbor_ip = DUT_EDGE.get_new_bgp_neighbor_ip()
    print(DUT_EDGE.disable_md5_on_bgp_neighbor(neighbor_ip=neighbor_ip))


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
    IX_NETWORK = IxNetwork(clear_config=True)


def get_bgp_summary():
    print(DUT_EDGE.get_bgp_summary())


if __name__ == '__main__':
    create_edge(edge_id=240, enterprise_id=1)
    start_ix_network(enable_md5=False)