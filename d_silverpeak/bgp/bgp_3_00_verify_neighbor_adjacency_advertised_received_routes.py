from my_silverpeak.BGPEdge import BGPEdge, DEFAULT_BGP_INFORMATION, Ixia
import time
import copy
from ipaddress import ip_address

# Ixia Settings
# Config File
IX_NET_CONFIG_FILE = 'SP_bgp_3_00_verify_neighbor_adjacency_advertised_received_routes.ixncfg'

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


def restore_bgp_default_settings():
    # Restore Edge to its BGP Default Settings
    BGP_EDGE.set_bgp_settings(bgp_settings=DEFAULT_BGP_INFORMATION)


def disable_bgp():
    # Disable BGP once done
    BGP_EDGE.disable_bgp()


def do_advertise_routes_match(edges_routes):
    """
    Prints yes or no if IxNetwork IPv4 Unicast Routes IP's match with Velo BGP Neighbor Advertised Routes IPs
    :param edges_routes: <list> Velo BGP Neighbor Advertised Routes IPs
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_advertise_routes_ips = []
    for route in edges_routes:
        edge_advertise_routes_ips.append(route.split('/')[0])

    # # Initiate globals for testing.
    # # Comment out for iTest run
    # SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
    #                                      LogLevel=SessionAssistant.LOGLEVEL_INFO,
    #                                      ClearConfig=False)
    #
    # # Get IxNetwork object from Session
    # IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Get Default Vport Name, Default will be first in list
    vport_name = PORTS[0]['Name']
    vport = IXIA.IxNetwork.Vport.find(Name=vport_name)

    # Refresh the routes
    neighbor_range = vport.Protocols.find().Bgp.NeighborRange.find()
    neighbor_range.RefreshLearnedInfo()
    time.sleep(10)
    ipv4_unicast = vport.Protocols.find().Bgp.NeighborRange.find().LearnedInformation.Ipv4Unicast.find()

    # Create list of ips taken from Protocol -> BGP
    # -> DUT Port -> IPv4 Peers -> 'Internal - 192.168.144.2-1' -> Learned Routes
    ix_network_advertise_routes_ips = []
    for ip in ipv4_unicast:
        ix_network_advertise_routes_ips.append(ip.IpPrefix)

    # Check if the ips match, expecting to match to pass the test
    if edge_advertise_routes_ips == ix_network_advertise_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Advertise Routes IPs': edge_advertise_routes_ips})
    print({'IxNetwork Advertise Routes IPs': ix_network_advertise_routes_ips})


def do_received_routes_match(edges_routes):
    """
    Prints yes or no if IxNetwork Route Range IPs match with Velo BGP Recieved Routes IPs
    :param edges_routes: <list> Velo BGP Neighbor Received Routes
    :return: none
    """
    # Parameter 'edges_routes' comes from VC BGP Neighbor Advertised Function.
    # It is a list of ip address and sometimes they have the subnet mask ex. 4.2.2.2/32.
    # We want to remove the subnet mask from the string to make it easier to match.
    # We will strip the subnet mask from 'edges_routes' and only have the ips.
    edge_received_routes_ips = []
    for route in edges_routes:
        edge_received_routes_ips.append(route.split('/')[0])

    # Get Default Vport Name, Default will be first in list
    vport_name = PORTS[0]['Name']
    vport = IXIA.IxNetwork.Vport.find(Name=vport_name)
    route_ranges = vport.Protocols.find().Bgp.NeighborRange.find().RouteRange.find()

    # Gather Ix Network Routes IPs
    ix_network_received_routes_ips = []
    for route in route_ranges:
        number_of_routes = route.NumRoutes
        ip = ip_address(address=route.NetworkAddress)
        while number_of_routes > 0:
            ix_network_received_routes_ips.append(str(ip))
            # Increase IP by 256
            ip = ip + 256
            number_of_routes -= 1

    if edge_received_routes_ips == ix_network_received_routes_ips:
        print({'match': 'yes'})
    else:
        print({'match': 'no'})

    print({'Edge Received Routes IPs': edge_received_routes_ips})
    print({'IxNetwork Received Routes IPs': ix_network_received_routes_ips})


def get_bgp_neighbor_received_routes():
    BGP_EDGE.get_bgp_route_table()


def get_bgp_neighbor_advertised_routes():
    BGP_EDGE.get_bgp_route_table()


def get_bgp_summary():
    while True:
        try:
            BGP_EDGE.get_bgp_summary()
        except KeyError:
            time.sleep(10)
            continue
        break


def create_edge(edge_id, enterprise_id=None):
    global BGP_EDGE
    BGP_EDGE = BGPEdge(edge_id=edge_id, enterprise_id=None, ssh_port=None)

    # Enable bgp
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

