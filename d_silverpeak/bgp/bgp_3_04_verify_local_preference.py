from my_silverpeak.BGPEdge import BGPEdge, DEFAULT_BGP_INFORMATION, Ixia
import time
import copy


# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'bgp_3_00_verify_neighbor_adjacency_advertised_received_routes_SP.ixncfg'

# VPorts
PORTS = [{'Name': 'LAN',
          'Chassis IP': '10.255.224.70',
          'Card': 3,
          'Port': 1
          }]

# Object for SilverPeak
BGP_EDGE: BGPEdge

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


def stop_ix_network():
    """
    Stops IxNetwork and Restores Edge's BGP settings to its default
    :return: None
    """

    # Stop IxNetwork
    IXIA.stop_ix_network()

    # Restore Edge to its BGP Default Settings
    BGP_EDGE.set_bgp_settings(bgp_settings=DEFAULT_BGP_INFORMATION)


def create_edge(edge_id, enterprise_id=None):
    global BGP_EDGE
    # BGP_EDGE = BGPRoutingEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)
    BGP_EDGE = BGPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    temp_bgp_information = copy.deepcopy(DEFAULT_BGP_INFORMATION)
    # Test requirements:
    #   iBGP
    #
    # By default BGP is set to iBGP, no need to adjust temp_bgp_information

    BGP_EDGE.set_bgp_settings(bgp_settings=temp_bgp_information)
    time.sleep(5)

    # Disable BGP and Enable BGP, to clear Peer State
    BGP_EDGE.disable_bgp()
    time.sleep(10)
    BGP_EDGE.enable_bgp()
    time.sleep(30)


def set_local_preference(local_preference:int):
    BGP_EDGE.set_local_preference_on_bgp_peer(local_preference=local_preference)


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
    # start_ix_network()
    # BGP_EDGE.set_local_preference_on_bgp_peer(local_preference=60, bgp_peer_ip='192.168.131.99')

