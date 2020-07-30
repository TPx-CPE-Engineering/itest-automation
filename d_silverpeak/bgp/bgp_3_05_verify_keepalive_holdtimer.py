from my_silverpeak.BGPEdge import BGPEdge, DEFAULT_BGP_INFORMATION, Ixia
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_bgp_3_05_verify_keepalive_holdtimer.ixncfg'

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


def get_bgp_summary():
    while True:
        try:
            BGP_EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def start_ix_network(hold_timer=None):
    """
    Starts IxNetwork
    :return: None
    """
    global IXIA
    IXIA = Ixia()

    IXIA.start_ix_network(config=IX_NET_CONFIG_FILE,
                          vports=PORTS,
                          config_local=True,
                          hold_timer=hold_timer)


def stop_ix_network(port_map_disconnect=True):
    """
    Stops IxNetwork and Restores Edge's BGP settings to its default
    :return: None
    """

    # Stop IxNetwork
    IXIA.stop_ix_network(port_map_disconnect=port_map_disconnect)


def restore_bgp_default_settings():
    # Restore Edge to its BGP Default Settings
    BGP_EDGE.set_bgp_settings(bgp_settings=DEFAULT_BGP_INFORMATION)


def disable_bgp():
    # Disable BGP once done
    BGP_EDGE.disable_bgp()


def show_bgp_neighbors():
    """
    Outputs response from 'show bgp neighbors' CLI command
    :return:
    """
    response = BGP_EDGE.api.post_broadcast_cli(applianceIDsList=[BGP_EDGE.edge_id],
                                               commandList=['show bgp neighbors'])

    # Parse the data since it includes linefeeds but does not print them
    html_data = response.data[0]['result']
    html_data = html_data.strip("{\"show bgp neighbors\":\"\\}")
    data_list = html_data.split('\\n')
    for item in data_list:
        print(item)


def set_keep_alive_timer_on_bgp_peer(keep_alive_timer):
    BGP_EDGE.set_keep_alive_timer_on_bgp_peer(keep_alive_timer=keep_alive_timer)


def set_hold_timer_on_bgp_peer(hold_timer):
    BGP_EDGE.set_hold_timer_on_bgp_peer(hold_timer=hold_timer)


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
    create_edge(edge_id='18.NE', enterprise_id=None)
    show_bgp_neighbors()