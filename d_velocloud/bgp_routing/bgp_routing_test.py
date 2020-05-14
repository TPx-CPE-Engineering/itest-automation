from d_velocloud.my_velocloud.base_edge import BaseEdge
from ixnetwork_restpy import SessionAssistant, Files


class BGPRoutingEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True,
                         live_mode=True)


# Object for Velocloud
EDGE: BGPRoutingEdge

# Objects for Ixia IxNetwork
SESSION_ASSISTANT: SessionAssistant
IX_NETWORK: SessionAssistant.Ixnetwork


def load_and_start_ix_network_config(ix_network_config='Juan_ix_test.ixncfg'):
    # Initiate IxNetwork session
    global SESSION_ASSISTANT, IX_NETWORK
    SESSION_ASSISTANT = SessionAssistant(IpAddress='10.255.20.7',
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=True)

    IX_NETWORK = SESSION_ASSISTANT.Ixnetwork

    # Load Config
    IX_NETWORK.LoadConfig(Files(ix_network_config))

    # Start Test


def stop_ix_network_config():

    # Connect to Initiated IxNetwork session

    # Stop Test
    print('todo')


def get_bgp_neighbor_received_routes():
    print(EDGE.LiveMode.get_bgp_neighbor_received_routes(segment_id=0, neighbor_ip='192.168.144.2'))


def get_bgp_neighbor_advertised_routes():
    print(EDGE.LiveMode.get_bgp_neighbor_advertised_routes(segment_id=0, neighbor_ip='192.168.144.2'))


def get_bgp_summary():
    print(EDGE.LiveMode.get_bgp_summary())


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = BGPRoutingEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0)


if __name__ == '__main__':
    create_edge(edge_id=3, enterprise_id=1)
    get_bgp_neighbor_advertised_routes()
