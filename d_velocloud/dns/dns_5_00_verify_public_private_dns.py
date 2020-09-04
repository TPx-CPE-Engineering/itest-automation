from my_velocloud.BaseEdge import BaseEdge
from velocloud.rest import ApiException

"""
Written by: juan.brena@tpx.com
Date: 2/11/2020

Revised:

Test Case places 2 Test Cases into one for simplicity. 

Test Case 1: 
Test Case: Verify private DNS from CPE behind VCE
Usage: Configure Edge to use 'Lab DNS' for Conditional DNS Forwarding (Edge > Device > DNS Settings > 
Conditional DNS Forwarding) 
Expected Results: Able to ping an private FQDN: lookup.test.lan, look510.test.lan

Test Case 2:
Test Case: Verify public DNS from CPE behind VCE
Usage: Configure Edge to use 'Google' Public DNS (Edge > Device > DNS Settings > Public DNS)
Expected Results: Abel to ping a public FQDN: tpx.com
"""


class DNSEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)

    def set_conditional_dns_forwarding_to_lab_dns(self):
        """
        Sets DNS Conditional DNS Forwarding to Lab DNS on the Enterprise Configuration Profile

        Within GUI: Configure > Profiles > Edge's Enterprise Profile > Device > DNS Settings >
        Conditional DNS Forwarding > Lab DNS
        """

        self.refresh_configuration_stack()

        # Get Enterprise's deviceSettings (ds) module
        enterprise_ds_module = self.get_module_from_enterprise_profile(module_name='deviceSettings').to_dict()

        ds_module_refs = enterprise_ds_module['refs']

        lab_dns_settings = {'configurationId': 10,
                            'enterpriseObjectId': 2967,
                            'logicalId': '1649888d-cbf9-419a-aff0-fc01c0f87003',
                            'moduleId': 57,
                            'ref': 'deviceSettings:dns:privateProviders',
                            'segmentLogicalId': '5dcc72f7-ed23-4bb1-9b7a-c5269d651a05',
                            'segmentObjectId': 15
                            }

        if 'deviceSettings:dns:privateProviders' not in ds_module_refs.keys():
            ds_module_refs['deviceSettings:dns:privateProviders'] = lab_dns_settings

            # Due to VCO update 3.4.x, Velo does not want Id, Type, or ConfigurationId to be passed to api push command
            # due to security reasons. So pop them off.
            enterprise_id = enterprise_ds_module['id']
            enterprise_ds_module.pop('id')
            enterprise_ds_module.pop('type')
            enterprise_ds_module.pop('configurationId')

            param = {'id': enterprise_id, 'enterpriseId': self.enterprise_id,
                     '_update': enterprise_ds_module}

            # Push change
            try:
                res = EDGE.api.configurationUpdateConfigurationModule(param)
                print(res)
            except ApiException as e:
                print(e)

    def set_conditional_dns_forwarding_to_none(self):
        """
        Sets DNS Conditional DNS Forwarding to [none] on the Enterprise Configuration Profile

        Within GUI: Configure > Profiles > Edge's Enterprise Profile > Device > DNS Settings >
        Conditional DNS Forwarding > [none]
        """
        self.refresh_configuration_stack()

        # Get Enterprise's deviceSettings (ds) module
        enterprise_ds_module = self.get_module_from_enterprise_profile(module_name='deviceSettings').to_dict()

        ds_module_refs = enterprise_ds_module['refs']

        if not ds_module_refs.pop('deviceSettings:dns:privateProviders', None):
            return

        # Due to VCO update 3.4.x, Velo does not want Id, Type, or ConfigurationId to be passed to api push command
        # due to security reasons. So pop them off.
        enterprise_id = enterprise_ds_module['id']
        enterprise_ds_module.pop('id')
        enterprise_ds_module.pop('type')
        enterprise_ds_module.pop('configurationId')

        param = {'id': enterprise_id, 'enterpriseId': self.enterprise_id, '_update': enterprise_ds_module}

        # Push change
        try:
            res = EDGE.api.configurationUpdateConfigurationModule(param)
            print(res)
        except ApiException as e:
            print(e)

    def is_conditional_dns_forwarding_set_to_lab_dns(self):
        """
        Prints yes or no (in json format) whether the Edge's Enterprise Configuration Profile's
        DNS Conditional Forwarding set to Lab DNS

        Within GUI: Configure > Profiles > Edge's Enterprise Profile > Device > DNS Settings>
        Conditional DNS Forwarding > Lab DNS
        """

        self.refresh_configuration_stack()

        # Get Enterprise's deviceSettings (ds) module
        enterprise_ds_module = self.get_module_from_enterprise_profile(module_name='deviceSettings').to_dict()

        # Get refs
        ds_module_refs = enterprise_ds_module['refs']

        # Check for private provider
        d = {'is_conditional_dns_forwarding_set_to_lab_dns': None}
        if 'deviceSettings:dns:privateProviders' in ds_module_refs.keys():
            d['is_conditional_dns_forwarding_set_to_lab_dns'] = 'yes'
        else:
            d['is_conditional_dns_forwarding_set_to_lab_dns'] = 'no'

        print(d)


EDGE: DNSEdge


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = DNSEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def set_conditional_dns_forwarding_to_lab_dns():
    EDGE.set_conditional_dns_forwarding_to_lab_dns()


def set_conditional_dns_forwarding_to_none():
    EDGE.set_conditional_dns_forwarding_to_none()


def is_conditional_dns_forwarding_set_to_lab_dns():
    EDGE.is_conditional_dns_forwarding_set_to_lab_dns()


if __name__ == '__main__':
    create_edge(edge_id='239', enterprise_id='1', ssh_port='2201')
    set_conditional_dns_forwarding_to_lab_dns()
