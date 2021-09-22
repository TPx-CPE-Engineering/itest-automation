from .business_policy_class import BPVeloCloudEdge as BPVeloCloudEdge_
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

    def set_wan_link_backup(self, is_enabled:bool, interface_name='TPx Communications'):
        wan_module = self.get_module_from_edge_specific_profile(module_name='WAN')
        # Look for the wan interface that matches parameter interface_name
        for link in wan_module['data']['links']:
            if link['name'].lower() == interface_name.lower():
                link['backupOnly'] = is_enabled

        return self.update_configuration_module(module=wan_module)

    def get_edge_model_number(self):
        method = 'edge/getEdge'
        params = {'id': self.id,
                  'enterpriseId': self.enterprise_id}

        edge_data = self.client.call_api(method=method, params=params)
        return edge_data['modelNumber'].strip('edge')

    def get_wan_link_backup_state(self, wan_link_name):
        method = 'edge/getEdge'
        params = {'id': self.id,
                  'enterpriseId': self.enterprise_id,
                  'with': ['links', 'recentLinks']}

        edge_data = self.client.call_api(method=method, params=params)

        for link in edge_data['recentLinks']:
            if link['displayName'] == wan_link_name:
                return link['backupState']

        wan_link_error = f'No WAN link named: "{wan_link_name}" found within the Edge. Please check the Edge.'
        return wan_link_error

    def check_for_link_dead_link_alive_events(self, start_interval):
        events = self.get_enterprise_events(start_interval=start_interval)

        response = {'LINK DEAD Present': False,
                    'LINK ALIVE Present': False}
        for event in events['data']:
            if event['event'] == 'LINK_DEAD':
                response['LINK DEAD Present'] = True
            elif event['event'] == 'LINK_ALIVE':
                response['LINK ALIVE Present'] = True

        return response

    def print_events(self, start_interval):
        events = self.get_enterprise_events(start_interval=start_interval)
        print(json.dumps(events['data'], indent=2))


if __name__ == '__main__':
    # Using edge: Single VCE640 (edge id: 247) has TEST EDGE
    edge = BPVeloCloudEdge(edge_id=247, enterprise_id=1)