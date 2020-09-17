from my_velocloud.VelocloudEdge import BGPVeloCloudEdge
from d_ixia.ix_network.Ix_Network import IxNetwork


# Ixia Settings
ix_network_config = 'bgp_3_00_verify_neighbor_adjacency_advertised_received_routes_VC.ixncfg'

# VPorts
vports = [{'Name': 'LAN',
           'Chassis IP': '10.255.224.70',
           'Card': 3,
           'Port': 3
           }]

DUT_EDGE: BGPVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ixia():
    IX_NETWORK.start_bgp_ix_network(config=ix_network_config, vports=vports, config_local=False,
                                    ipv4_address='192.168.136.2', ipv4_mask_width='24', ipv4_gateway='192.168.136.1')


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = BGPVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # For this test ...
    # Enable BGP on Enterprise profile
    DUT_EDGE.enable_bgp_on_enterprise_segment()

    # Initiate Ix Network
    # IX_NETWORK = IxNetwork()
    # import json
    # print(json.dumps(DUT_EDGE.default_bgp_segment, sort_keys=True, indent=4))

    # DUT_EDGE.overwrite_bgp_neighbor(neighbor_ip='192.168.33.2', neighbor_asn='65535')


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    # start_ixia()
