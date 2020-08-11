from my_silverpeak.OSPFEdge import OSPFEdge, Ixia
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


def get_ospf_neighbors():
    response = OSPF_EDGE.api.get_ospf_state_neighbors(applianceID=OSPF_EDGE.edge_id)
    print(json.dumps(response.data))


def create_edge(edge_id, enterprise_id=None):
    global OSPF_EDGE
    OSPF_EDGE = OSPFEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)


if __name__ == '__main__':
    Edge = OSPFEdge(edge_id='18.NE', enterprise_id=None, ssh_port=None)
    res = Edge.api.get_ospf_state_neighbors(applianceID=Edge.edge_id)
    print(res)
