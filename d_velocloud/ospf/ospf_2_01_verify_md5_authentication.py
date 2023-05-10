from my_velocloud.VelocloudEdge import OSPFVeloCloudEdge
from ix_network.Ix_Network import IxNetwork
from ipaddress import ip_address
import time

DUT_EDGE: OSPFVeloCloudEdge
IX_NETWORK: IxNetwork
OSPF_INTERFACE = None


# noinspection PyUnresolvedReferences
def start_ix_network(enable_ospf_md5, key_id=None, password=None):
    ix_network_config = 'VC_ospf_2_01_verify_md5_authentication.ixncfg'

    ospf_interface_cidr = OSPF_INTERFACE['addressing']['cidrIp']

    # Set Ix Network IP
    # It will be Ix Network Gateway plus 1
    ip = ip_address(address=ospf_interface_cidr)
    ipv4_address = str(ip + 1)

    if enable_ospf_md5:
        authentication_method = 'md5'
    else:
        authentication_method = 'null'

    IX_NETWORK.start_ospf(config=ix_network_config,
                          config_local=True,
                          ipv4_address=ipv4_address,
                          ipv4_mask_width='24',
                          ipv4_gateway=ospf_interface_cidr,
                          authentication_method=authentication_method,
                          md5_key=password,
                          md5_key_id=key_id
                          )


def stop_ix_network(disconnect_ports=True):
    IX_NETWORK.stop_ix_network(port_map_disconnect=disconnect_ports)


def restore_settings():
    file = 'C:/Users/dataeng/PycharmProjects/iTest_Automation/d_velocloud/ospf/ospf_device_settings.json'
    print(DUT_EDGE.restore_config_from_filename(filename=file))
    DUT_EDGE.delete_filename(filename=file)


def disable_ospf_md5_auth():
    print(DUT_EDGE.disable_ospf_md5_authentication(ospf_interface_name=OSPF_INTERFACE['name']))


# noinspection PyUnresolvedReferences
def enable_ospf_md5_auth(key_id, password):
    print(DUT_EDGE.enable_ospf_md5_authentication(ospf_interface_name=OSPF_INTERFACE['name'],
                                                  key_id=key_id,
                                                  password=password))


def get_ospf_neighbors_count():
    ospf_neighbors = DUT_EDGE.get_ospf_neighbors()
    print(len(ospf_neighbors))


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, IX_NETWORK, OSPF_INTERFACE
    DUT_EDGE = OSPFVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)

    # Save settings before modifying in order to reformat Edge
    DUT_EDGE.save_module_to_restore(module_name='deviceSettings', path='C:/Users/dataeng/PycharmProjects/iTest_Automation/d_velocloud/ospf/',
                                    filename='ospf_device_settings')

    # Steps to configure edge for OSPF
    # Find a Interface that is in VLAN ID 1, in this case it'll be 'GE2'
    OSPF_INTERFACE = DUT_EDGE.get_ospf_interface_config(vlan_id=1)
    print('Adding \'{}\' as a static interface with IP Address \'{}\' for OSPF testing...'.format(
        OSPF_INTERFACE['name'], OSPF_INTERFACE['addressing']['cidrIp']
    ))

    # Add Interface Config to Edge
    print(DUT_EDGE.add_routed_interface(interface=OSPF_INTERFACE, vlan_id=1))

    # Initiate Ix Network
    IX_NETWORK = IxNetwork(clear_config=True)


if __name__ == '__main__':
    create_edge(edge_id=4, enterprise_id=1)
    time.sleep(10)
    disable_ospf_md5_auth()
    time.sleep(5)
    start_ix_network(enable_ospf_md5=False)
    time.sleep(5)
    get_ospf_neighbors_count()
    time.sleep(5)
    stop_ix_network()
