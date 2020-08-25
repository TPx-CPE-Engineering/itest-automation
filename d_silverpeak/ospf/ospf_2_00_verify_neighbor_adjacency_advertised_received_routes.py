from my_silverpeak.OSPFEdge import OSPFEdge, Ixia, DEFAULT_OSPF_INFORMATION
import json
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
                          config_local=False)


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


def get_ospf_received_routes():
    # Get default interface
    interface_name = None
    try:
        interface_name = DEFAULT_OSPF_INFORMATION['Interfaces'][0]['lan0']['self']
    except KeyError as e:
        print('Please verify DEFAULT_OSPF_INFORMATION interface: \'lan0\' exists.'
              'If default interface changed please update here too.')

    # Getting all routes
    response = OSPF_EDGE.api.get_subnets(applianceID=OSPF_EDGE.edge_id)

    received_routes = []
    # Filter routes based based on default interface
    for entry in response.data['subnets']['entries']:
        if entry['state']['ifName'] == interface_name:
            # Ignore '192.168.x.x' route
            if '192.168.' not in entry['state']['prefix']:
                received_routes.append(entry['state']['prefix'])

    print(json.dumps(received_routes))


def create_edge(edge_id, enterprise_id=None):
    global OSPF_EDGE
    OSPF_EDGE = OSPFEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)


if __name__ == '__main__':
    OSPF_EDGE = OSPFEdge(edge_id='18.NE', enterprise_id=None, ssh_port=None)
    get_ospf_neighbor_count()
