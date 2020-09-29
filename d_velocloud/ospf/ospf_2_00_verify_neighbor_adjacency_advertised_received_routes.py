from my_velocloud.VelocloudEdge import OSPFVeloCloudEdge
from ix_network.Ix_Network import IxNetwork

DUT_EDGE: OSPFVeloCloudEdge
IX_NETWORK: IxNetwork


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = OSPFVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # Initiate Ix Network
    IX_NETWORK = IxNetwork(clear_config=True)


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)