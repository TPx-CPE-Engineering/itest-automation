from my_silverpeak.BGPEdge import BGPEdge, DEFAULT_BGP_INFORMATION, Ixia
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_bgp_3_01_verify_md5_authentication.ixncfg'

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


# noinspection PyTypeChecker
def start_ix_network(enable_md5=False, md5_password=None):
    """
    Starts IxNetwork
    :return: None
    """
    global IXIA
    IXIA = Ixia()

    IXIA.start_ix_network(config=IX_NET_CONFIG_FILE,
                          vports=PORTS,
                          config_local=False,
                          enable_md5=enable_md5,
                          md5_password=md5_password)


def stop_ix_network(set_bgp_default_settings=True):
    """
    Stops IxNetwork and Restores Edge's BGP settings to its default
    :return: None
    """

    # Stop IxNetwork
    IXIA.stop_ix_network()


def restore_bgp_default_settings():
    # Restore Edge to its BGP Default Settings
    BGP_EDGE.set_bgp_settings(bgp_settings=DEFAULT_BGP_INFORMATION)


def disable_bgp():
    # Disable BGP once done
    BGP_EDGE.disable_bgp()


def get_bgp_summary():
    while True:
        try:
            BGP_EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def disable_bgp_md5_auth():
    BGP_EDGE.disable_bgp_md5_auth()


def enable_bgp_md5_auth(password):
    BGP_EDGE.enable_bgp_md5_auth(password=password)


def create_edge(edge_id, enterprise_id=None):
    global BGP_EDGE
    BGP_EDGE = BGPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    BGP_EDGE.enable_bgp()
    time.sleep(15)

    temp_bgp_information = copy.deepcopy(DEFAULT_BGP_INFORMATION)
    # Test requirements:
    #   iBGP
    #
    # By default BGP is set to iBGP

    BGP_EDGE.set_bgp_settings(bgp_settings=temp_bgp_information)
    time.sleep(20)


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
    # get_bgp_neighbor_advertised_routes()
    BGP_EDGE.enable_bgp_md5_auth(password='maule123')
    # BGP_EDGE.disable_bgp_md5_auth()
