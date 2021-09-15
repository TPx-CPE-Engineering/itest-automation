from my_velocloud.VelocloudEdge import VeloCloudEdge
from ipaddress import ip_address
import json


class BPVeloCloudEdge(VeloCloudEdge):
    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

    # Any related to Business Policy(BP) test case/s you can add it here
    def get_active_wan_interfaces(self):
        wan_settings = self.get_module_from_edge_specific_profile(module_name='WAN')
        for link in wan_settings['data']['links']:
            link['isLinkIpAddressPublic'] = not ip_address(link['publicIpAddress']).is_private
        return json.dumps(wan_settings['data']['links'])


if __name__ == '__main__':
    edge = BPVeloCloudEdge(edge_id=245, enterprise_id=1)
