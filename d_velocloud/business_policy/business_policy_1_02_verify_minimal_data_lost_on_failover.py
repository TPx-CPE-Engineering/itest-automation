from business_policy_class import BPVeloCloudEdge as BPVeloCloudEdge_
import json


class BPVeloCloudEdge(BPVeloCloudEdge_):
    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

    def get_wan_link(self, wan_link_name='TPx Communications'):
        wan_settings = self.get_module_from_edge_specific_profile(module_name='WAN')

        # Look for the wan interface that matches parameter interface_name
        for link in wan_settings['data']['links']:
            if link['name'].lower() == wan_link_name.lower():
                return link

    def is_wan_link_set_as_backup(self, wan_link_name='TPx Communications'):
        wan_link = self.get_wan_link(wan_link_name=wan_link_name)
        # Check if the wan interface is set as backup
        return json.dumps(wan_link['backupOnly'])

    def set_wan_interface_backup(self, is_enabled:bool,interface_name='TPx Communications'):
        wan_module = self.get_module_from_edge_specific_profile(module_name='WAN')
        # Look for the wan interface that matches parameter interface_name
        print(wan_module)
        exit()
        for link in wan_module['data']['links']:
            if link['name'].lower() == interface_name.lower():
                link['backupOnly'] = is_enabled

        r = self.update_configuration_module(module=wan_module)

    def get_edge_model_number(self):
        method = 'edge/getEdge'
        params = {'id': self.id,
                  'enterpriseId': self.enterprise_id}

        edge_data = self.client.call_api(method=method, params=params)
        return edge_data['modelNumber'].strip('edge')


if __name__ == '__main__':
    # Using edge: Single VCE610 has TEST EDGE
    edge = BPVeloCloudEdge(edge_id=221, enterprise_id=1)
    edge.set_wan_interface_backup(is_enabled=False)