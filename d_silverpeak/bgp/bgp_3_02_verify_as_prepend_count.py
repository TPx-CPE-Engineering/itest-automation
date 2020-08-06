from my_silverpeak.BGPEdge import BGPEdge, DEFAULT_BGP_INFORMATION, Ixia
import time
import copy

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_bgp_3_02_verify_as_prepend_count.ixncfg'

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


def set_as_prepend_count(count:int):
    BGP_EDGE.set_as_prepend_count_on_bgp_peer(as_prepend_count=count)


def do_ix_network_routes_match_as_prepend_count(count:int):
    # Get Default Vport Name, Default will be first in list
    vport_name = PORTS[0]['Name']
    vport = IXIA.IxNetwork.Vport.find(Name=vport_name)

    # Refresh routes
    neighbor_range = vport.Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()
    time.sleep(5)

    ipv4_unicast = vport.Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    match_as_prepend_count = True
    for ip in ipv4_unicast:
        as_path = ip.AsPath.strip("<>").split(" ")
        if not len(as_path) == count + 1:
            match_as_prepend_count = False
            break

    if match_as_prepend_count:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    routes = []
    for ip in ipv4_unicast:
        routes.append({'IP': ip.IpPrefix + '/' + str(ip.PrefixLength), 'AsPath': ip.AsPath})
    print(routes)


def create_edge(edge_id, enterprise_id=None):
    global BGP_EDGE
    BGP_EDGE = BGPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    BGP_EDGE.enable_bgp()
    time.sleep(15)

    temp_bgp_information = copy.deepcopy(DEFAULT_BGP_INFORMATION)
    # Test requirements:
    #   eBGP
    #
    # By default BGP is set to iBGP
    # For eBGP, Edge ASN must be different than the Peer ASN

    # Grab default Peer IP, default Peer is the first in the list, Silverpeak uses its IP as key for dict.
    default_peer = temp_bgp_information['BGP Peers'][0]
    default_peer_ip = next(iter(default_peer))

    # Set Config System ASN to BGP Peer ASN + 1 in order to be different and have eBGP
    temp_bgp_information['Config System']['asn'] = default_peer[default_peer_ip]['remote_as'] + 1

    BGP_EDGE.set_bgp_settings(bgp_settings=temp_bgp_information)
    time.sleep(20)


if __name__ == '__main__':
    create_edge(edge_id='18.NE')
