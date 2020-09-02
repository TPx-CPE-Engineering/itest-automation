from my_silverpeak.OSPFEdge import OSPFEdge, Ixia, DEFAULT_OSPF_INFORMATION
import json
from ipaddress import ip_address
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_ospf_2_01_verify_md5_authentication.ixncfg'

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


def start_ix_network(enable_ospf_md5=False, key_id='1', password='maule123'):
    """
    Starts IxNetwork
    :return: None
    """
    global IXIA
    IXIA = Ixia()

    IXIA.start_ix_network(config=IX_NET_CONFIG_FILE,
                          vports=PORTS,
                          config_local=True,
                          enable_md5=enable_ospf_md5,
                          md5_password=password,
                          md5_key=key_id)


def stop_ix_network(disconnect_ports=True):
    """
    Stops IxNetwork
    :return: None
    """

    # Stop IxNetwork
    try:
        global IXIA
        IXIA.stop_ix_network(port_map_disconnect=disconnect_ports)
    except NameError:
        IXIA = Ixia(clear_config=False)
        IXIA.stop_ix_network()


def disable_ospf_md5_auth():
    OSPF_EDGE.disable_ospf_md5_auth()


def enable_ospf_md5_auth(key_id, password):
    OSPF_EDGE.enable_ospf_md5_auth(md5_password=password, md5_key=key_id)


def create_edge(edge_id, enterprise_id=None):
    global OSPF_EDGE
    OSPF_EDGE = OSPFEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    OSPF_EDGE.enable_ospf()
    time.sleep(15)

    # Test requirements:
    #   Enable OSPF to OSPF Defaults

    OSPF_EDGE.set_ospf_settings_to_default()
    time.sleep(20)


if __name__ == '__main__':
    OSPF_EDGE = OSPFEdge(edge_id='18.NE', enterprise_id=None, ssh_port=None)
    enable_ospf_md5_auth(key_id='1', password='maule123')