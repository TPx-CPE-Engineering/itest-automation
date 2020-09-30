from my_velocloud.VelocloudEdge import OSPFVeloCloudEdge
from ix_network.Ix_Network import IxNetwork
import time
from ipaddress import ip_address

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
                          config_local=False,
                          ipv4_address=str(ip),
                          ipv4_mask_width='24',
                          ipv4_gateway=corporate_vlan_ip_address)


def stop_ix_network():
    IX_NETWORK.stop_ix_network()

    restore_settings()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK
    DUT_EDGE = OSPFVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # Steps to configure edge for OSPF
    # Find a Interface that is in the Global Segment Interfaces, in this case it'll be 'GE2'
    interface_config = DUT_EDGE.get_ospf_interface_config()
    print('Adding \'{}\' as a static interface with IP Address \'{}\' for OSPF testing...'.format(
        interface_config['name'], interface_config['addressing']['cidrIp']
    ))

    # Add Interface Config to Edge
    print(DUT_EDGE.add_routed_interface(interface=interface_config))

    # Initiate Ix Network
    IX_NETWORK = IxNetwork(clear_config=True)


def restore_settings():
    file = 'ospf_device_settings.txt'
    print(DUT_EDGE.restore_config_from_filename(filename=file))
    DUT_EDGE.delete_filename(filename=file)


def verify_if_advertised_routes_match():
    routes = get_advertised_routes()

    for route in routes:
        print(route)


def get_advertised_routes():
    response = DUT_EDGE.get_ospf_database()
    print(response)
    print('\n\n\n')
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


def get_ospf_neighbors():
    response = DUT_EDGE.get_ospf_neighbors()
    response_lines = response.splitlines()

    # Find header start
    header_start = 0
    for item in range(0, len(response_lines)):
        if 'Neighbor ID' in response_lines[item] and 'Pri' in response_lines[item] and 'Dead' in response_lines[item]:
            header_start = item

    routes = []
    # Get all entries after the table header
    for line in response_lines[header_start + 1:]:
        line_split = line.split()
        if len(line_split) == 9:
            entry = {
                'Neighbor ID': line_split[0],
                'Pri': line_split[1],
                'State': line_split[2],
                'Dead Time': line_split[3],
                'Address': line_split[4],
                'Interface': line_split[5],
                'RXmtL': line_split[6],
                'RqstL': line_split[7],
                'DBsmL': line_split[8]
            }
            routes.append(entry)

    return routes


def get_ospf_neighbors_count():
    ospf_neighbors = get_ospf_neighbors()
    print(len(ospf_neighbors))


if __name__ == '__main__':
    create_edge(edge_id=221, enterprise_id=1)
    print(get_ospf_neighbors_count())