#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge
import time

"""
Written by: juan.brena@tpx.com
Date: 2/11/2020

Revised:

Test Case places 2 Test Cases into one for simplicity. 

Test Case 1: 
Test Case: Verify private DNS from CPE behind VCE
Usage: Configure Edge to use 'Lab DNS' for Conditional DNS Forwarding (Edge > Device > DNS Settings > Conditional DNS Forwarding) 
Expected Results: Able to ping an private FQDN: lookup.test.lan, look510.test.lan

Test Case 2:
Test Case: Verify public DNS from CPE behind VCE
Usage: Configure Edge to use 'Google' Public DNS (Edge > Device > DNS Settings > Public DNS)
Expected Results: Abel to ping a public FQDN: tpx.com
"""


class DNSEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)

    def set_conditional_dns_forwarding_to_default(self):
        """
        Sets Edge's Conditional DNS Forwarding to default which should be to Lab DNS

        This is done by removing Edge Override, thus Edge will default to Enterprise profile
        """

        # Get Edge's Device Specific Device Settings module
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Filter through Device Setting's (ds) segments and grab Global Segment
        ds_global_segment = None
        for seg in device_settings_module.data['segments']:
            if seg['segment']['name'] == 'Global Segment':
                ds_global_segment = seg

        # Pop 'dns' key to remove
        if not ds_global_segment.pop('dns', None):
            d = {'error': None, 'rows': 0, 'message': "Conditional DNS Forwarding already set to Default"}
            print(d)
            return

        # Set api parameters
        print('ID: {}'.format(device_settings_module.id))
        param = ConfigurationUpdateConfigurationModule(id=device_settings_module.id, enterpriseId=self.enterprise_id, update=device_settings_module)

        # Push change
        res = api.configurationUpdateConfigurationModule(param)

        # Print response
        print(res)

    def set_conditional_dns_forwarding_to_none(self):
        """
        Enables Edge Override and Sets Edge's Conditional DNS Forwarding to '[none]'

        Edge > Device > DNS Settings > Conditional DNS Forwarding > [none]
        """

        # Get Edge's Device Specific deviceSettings module (ds)
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get ds data
        ds_module_data = device_settings_module.data

        # Filter through ds segments and grab 'Global Segment'
        ds_global_segment = None
        for seg in ds_module_data['segments']:
            if seg['segment']['name'] == 'Global Segment':
                ds_global_segment = seg

        # Set configuration settings so Conditional DNS Forwarding be set to '[none]'
        # Within GUI: Edge > Device > DNS Settings > Enable 'Enable Edge Override' > Set Conditional DNS Forwarding to [none]
        dns_none_settings = {'primaryProvider': {'ref': 'deviceSettings:dns:primaryProvider'},
                             'backupProvider': {'ref': 'deviceSettings:dns:backupProvider'},
                             'privateProviders': {'ref': 'deviceSettings:dns:privateProviders'},
                             'override': True}

        # Apply DNS configuration to ds Global Segment
        ds_global_segment['dns'] = dns_none_settings

        # Set api parameters
        param = {'enterpriseId': self.enterprise_id,
                 'id': device_settings_module.id,
                 '_update': {'data': ds_module_data}}

        # Push change
        res = api.configurationUpdateConfigurationModule(param)

        # Print response
        print(res)


EDGE: DNSEdge


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = DNSEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def set_conditional_dns_forwarding_to_default():
    EDGE.set_conditional_dns_forwarding_to_default()


def set_conditional_dns_forwarding_to_none():
    EDGE.set_conditional_dns_forwarding_to_none()


if __name__ == '__main__':
    create_edge(edge_id='1', enterprise_id='1', ssh_port='2201')
    set_conditional_dns_forwarding_to_none()

