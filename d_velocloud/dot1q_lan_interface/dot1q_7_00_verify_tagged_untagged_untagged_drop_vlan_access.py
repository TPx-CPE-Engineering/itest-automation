from my_velocloud.BaseEdge import BaseEdge
from velocloud import *


class DOT1QEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)

    def change_interface_untagged_vlan(self, interface_name, untagged_vlan):
        """
        Change Interface's Untagged VLAN to untagged_vlan
        :param interface_name: Interface you want to perform the action on
        :param untagged_vlan: Desired untagged_vlan option, either 'drop' or vlanId
        :return:
        """

        # Get Edge's edge specific device settings
        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get to the param:interface settings
        # And update its untaggedVlan property to param:untagged_vlan
        for interface in device_settings.data['lan']['interfaces']:
            if interface['name'] == interface_name:

                # If untagged vlan already set to param:untagged_vlan then return
                if interface['untaggedVlan'] == untagged_vlan:
                    print({'error': None, 'rows': 0})
                    return

                interface['untaggedVlan'] = untagged_vlan

        param = ConfigurationUpdateConfigurationModule(id=device_settings.id,
                                                       enterpriseId=self.enterprise_id,
                                                       update=ConfigurationModule(data=device_settings.data))

        response = EDGE.api.configurationUpdateConfigurationModule(param)

        print(response)


EDGE: DOT1QEdge


def create_edge(edge_id, enterprise_id):
    global EDGE
    EDGE = DOT1QEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=0)


def change_interface_untagged_vlan_to_vlan1527():
    EDGE.change_interface_untagged_vlan(interface_name='LAN2', untagged_vlan='1527')


def change_interface_untagged_vlan_to_drop():
    EDGE.change_interface_untagged_vlan(interface_name='LAN2', untagged_vlan='drop')


if __name__ == '__main__':
    create_edge(edge_id='1', enterprise_id='1')
    change_interface_untagged_vlan_to_vlan1527()
