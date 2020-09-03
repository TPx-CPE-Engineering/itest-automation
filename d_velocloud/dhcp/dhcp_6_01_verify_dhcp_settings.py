from velocloud.models import *
from my_velocloud.BaseEdge import BaseEdge

"""
Written by: juan.brena@tpx.com
Date: 2/11/2020

Revised:

Test Case places six Test Cases into one for simplicity. 

Velocloud
Test Case #1 <- TODO
Test Case: IP address/gateway assignment
Expected Results: Configure DHCP pool for LAN devices under Configure > Edge > Device > VLAN. Verify new devices get assigned addressed from pool.
Usage: Edge provides IP and Gateway IP to new devices

Test Case #2
Test Case: Option 66 (tftp)
Expected Results: Configure a value for tftp server and verify end device receives tftp address in DHCP offer. End device (CPE or IP Phone) must first be 
configured to request OPT 66, before it will get it from the VCE.
Usage: Edge provides an Option 66 with DHCP offer

Test Case #3
Test Case: Option 6 (DNS)
Expected Results: Configure a value for DNS and verify end device receives DNS server address in DHCP offer.
Usage: Edge provides an Option 6 with DHCP offer

Test Case #4
Test Case: Option 15(domain name)
Expected Results: Configure a value for domain name and verify end device receives a domain name in DHCP offer.
Usage: Edge provides an Option 15 with DHCP offer

Test Case #5
Test Case: Custom Option (160)
Expected Results: Configure a custom option with random text value and verify end device receives the custom option and value in DHCP offer (as before, CPE or
 IP phone must be configured to request OPT 160)
Usage: Edge provides a custom option with DHCP offer

Test Case #6
Test Case: Verify devices are assigned the same IP address when configured
Expected Results: Configure device MAC address and IP to be assigned in the "Fixed IP's" section.
Usage: Device will be assigned the same IP address every time

"""


class DHCPEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id,
                         enterprise_id=enterprise_id,
                         ssh_port=ssh_port)

    def add_dhcp_options(self) -> None:
        """
        Adds 4 options to the Edge's Voice VLAN DHCP Settings

        Configurations can be found in Edge > Device > Configure VLAN > 'Edit' Action for Voice VLAN > DHCP > Options
        Configurations that will be added are the following:
        Options             Code            Data Type           Value
        ----------------------------------------------------------
        DNS Server (6)      6               IP Address          3.3.3.3
        Domain Name (15)    15              Host                dnsdummy.com
        TFTP Server (66)    66              Text                6.6.6.6
        Custom              160             Text                dhcpdummy.com
        """

        # Get Edge's Device Specific Device Settings module
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get the LAN Networks from Device Settings module
        lan_networks = None
        try:
            lan_networks = device_settings_module.data['lan']['networks']
        except KeyError:
            print('KeyError')

        # Filter through the networks and get the 'Voice' LAN Network
        voice_lan_network = None
        for net in lan_networks:
            if net['name'] == self.voice_segment_name:
                voice_lan_network = net

        # Get DHCP from 'Voice' LAN Network
        dhcp_settings = voice_lan_network['dhcp']

        # Configure DHCP Settings
        dhcp_settings_opt_6 = {'option': 6,
                               'value': ['3.3.3.3'],
                               'type': 'ip',
                               'metaData': {'option': 6,
                                            'name': 'DNS Servers',
                                            'description': 'List of DNS server addresses',
                                            'dataType': 'ip',
                                            'list': True,
                                            'display': True
                                            }
                               }
        dhcp_settings_opt_15 = {'option': 15,
                                'value': ['dnsdummy.com'],
                                'type': 'name',
                                'metaData': {'option': 15,
                                             'name': 'DNS Name',
                                             'description': 'DNS domain name of the client',
                                             'dataType': 'name',
                                             'list': True,
                                             'display': True
                                             }
                                }
        dhcp_settings_opt_66 = {'option': 66,
                                'value': '6.6.6.6',
                                'type': 'text',
                                'metaData': {'option': 66,
                                             'name': 'TFTP Server',
                                             'description': 'Used when SNAME field is used in the DHCP header',
                                             'dataType': 'text',
                                             'list': False,
                                             'display': True
                                             }
                                }
        dhcp_settings_opt_160 = {'option': 160,
                                 'value': 'dhcpdummy.com',
                                 'type': 'text'
                                 }

        # Put DHCP Settings into a list
        dhcp_options = [dhcp_settings_opt_6, dhcp_settings_opt_15, dhcp_settings_opt_66, dhcp_settings_opt_160]

        # Insert DHCP Settings
        dhcp_settings['options'] = dhcp_options

        # Set api parameters
        param = ConfigurationUpdateConfigurationModule(id=device_settings_module.id,
                                                       enterpriseId=self.enterprise_id,
                                                       update=ConfigurationModule(data=device_settings_module.data))

        # Push change
        res = EDGE.api.configurationUpdateConfigurationModule(param)

        # Print response
        print(res)

    def remove_dhcp_options(self) -> None:
        """
        Removes the 4 configurations added by add_dhcp_options
        """
        # Get Edge's Device Specific Device Settings module
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get the LAN Networks from Device Settings module
        lan_networks = None
        try:
            lan_networks = device_settings_module.data['lan']['networks']
        except KeyError:
            print('KeyError')

        # Filter through the networks and get the 'Voice' LAN Network
        voice_lan_network = None
        for net in lan_networks:
            if net['name'] == self.voice_segment_name:
                voice_lan_network = net

        # Get DHCP from 'Voice' LAN Network
        dhcp_settings = voice_lan_network['dhcp']

        # Clear DHCP Settings
        dhcp_settings['options'] = []

        # Set api parameters
        param = ConfigurationUpdateConfigurationModule(id=device_settings_module.id,
                                                       enterpriseId=self.enterprise_id,
                                                       update=ConfigurationModule(data=device_settings_module.data))

        # Push change
        res = EDGE.api.configurationUpdateConfigurationModule(param)

        # Print response
        print(res)

    def are_dhcp_options_empty(self) -> None:
        """
        Prints yes or no whether the Edge has no DHCP options
        """
        # Get Edge's Device Specific Device Settings module
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Get the LAN Networks from Device Settings module
        lan_networks = None
        try:
            lan_networks = device_settings_module.data['lan']['networks']
        except KeyError:
            print('KeyError')

        # Filter through the networks and get the 'Voice' LAN Network
        voice_lan_network = None
        for net in lan_networks:
            if net['name'] == self.voice_segment_name:
                voice_lan_network = net

        # Get DHCP from 'Voice' LAN Network
        dhcp_settings = voice_lan_network['dhcp']

        if not dhcp_settings['options']:
            d = {'are_dhcp_options_empty': 'yes', 'number_of_options': len(dhcp_settings['options'])}
            print(d)
        else:
            d = {'are_dhcp_options_empty': 'no', 'number_of_options': len(dhcp_settings['options'])}
            print(d)


EDGE: DHCPEdge


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = DHCPEdge(edge_id=int(edge_id),
                    enterprise_id=int(enterprise_id),
                    ssh_port=int(ssh_port))


def add_dhcp_options() -> None:
    EDGE.add_dhcp_options()


def remove_dhcp_options() -> None:
    EDGE.remove_dhcp_options()


def are_dhcp_options_empty() -> None:
    EDGE.are_dhcp_options_empty()


if __name__ == '__main__':
    create_edge(edge_id='1',
                enterprise_id='1',
                ssh_port='2201')

    are_dhcp_options_empty()
