from my_velocloud.VelocloudEdge import OSPFVeloCloudEdge
from ix_network.Ix_Network import IxNetwork
import time

DUT_EDGE: OSPFVeloCloudEdge
IX_NETWORK: IxNetwork


def start_ix_network():
    ix_network_config = 'VC_ospf_2_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

    corporate_vlan = DUT_EDGE.get_vlan(vlan_id=1)

    # Get IP Address of VLAN
    corporate_vlan_ip_address = corporate_vlan['cidrIp']

    IX_NETWORK.start_bgp_ix_network(config=ix_network_config,
                                    config_local=True,
                                    ipv4_address=ipv4_address,
                                    ipv4_mask_width='24',
                                    ipv4_gateway=ipv4_gateway)


def stop_ix_network():
    IX_NETWORK.stop_ix_network()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = OSPFVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # Steps to configure edge for OSPF
    # Find a Interface that is in the Global Segment Interfaces, in this case it'll be 'GE2'
    interface_config = DUT_EDGE.get_ospf_interface_config()
    print('Adding \'{}\' as a static interface with IP Address \'{}\' for OSPF testing...'.format(
        interface_config['name'], interface_config['addressing']['cidrIp']
    ))

    print(DUT_EDGE.add_routed_interface(interface=interface_config))

    # # Initiate Ix Network
    # IX_NETWORK = IxNetwork(clear_config=True)


def restore_settings():
    file = 'ospf_device_settings.txt'
    print(DUT_EDGE.restore_config_from_filename(filename=file))
    DUT_EDGE.delete_filename(filename=file)


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
