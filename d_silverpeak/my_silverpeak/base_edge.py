from my_silverpeak import operator_login
import json

"""
Base Edge template for Silverpeak automation
"""


class SPBaseEdge:
    def __init__(self, edge_id, enterprise_id, ssh_port, auto_operator_login=True):
        self.edge_id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port
        self.api = None
        self.cpe_lan_ip = None
        self.debug = False

        if auto_operator_login:
            self.api = operator_login.login()


        # Deployment Parameters
        self.default_fw_zone = {'name': 'Default',
                                'id': 0}

        self.testing_fw_zone = {'name': 'ONE',
                                'id': 12}

        self.testing_label = {'name': 'Voice',
                              'id': '4'}

        self.testing_interface = {'interface': 'lan0',
                                  'vlan': None,
                                  'fw_zone': self.testing_fw_zone,
                                  'label': self.testing_label,
                                  'ip/mask': None,
                                  'comment': 'itest'}

    def get_cpe_lan_ip(self):
        """
        Get the CPE's LAN IP (sitting behind Silverpeak Edge) by looking at the port forwarding rules and looking for port, protocol, and comment
        :return: CPE LAN IP or an empty str
        """

        # Check if cpe_lan_ip is already set
        if self.cpe_lan_ip:
            return self.cpe_lan_ip

        # Else find cpe_lan_ip
        # Get Port Forwarding Rules
        url = self.api.base_url + '/portForwarding/' + self.edge_id
        res = self.api._get(session=self.api.session, url=url, headers=None, timeout=10)
        port_forwarding_rules = res.data

        # Locate the SSH Port Forwarding Rules based on it its protocol destination port and it has itest in the comments
        for rule in port_forwarding_rules:
            if rule['protocol'] == 'tcp' and rule['destPort'] == self.ssh_port and 'itest' in rule['comment'].lower():
                return rule['targetIp']

        # If rule is not found then raise a KeyError
        raise KeyError("A SSH Inbound Forwarding Rule with Protocol = TCP, Destination Port = {}, and string 'itest' in the Comment was not found.".format(
            self.ssh_port))

    def set_testing_fw_zone_for_testing_interface(self):
        """
        Sets Deployment Parameter: self.testing_fw_zone for self.testing_interface FW Zone
        :return: Prints result
        """

        if self.debug:
            print("FW Zone '{} id:{]' for Interface '{}'".format(self.testing_fw_zone['name'],
                                                                 self.testing_fw_zone['id'],
                                                                 self.testing_interface['interface']))

        # Avoid setting fw zone if already set
        if self.is_testing_fw_zone_set_for_testing_interface():
            return

        # Get Edge's deployment data
        deployment = self.api.get_deployment_data(applianceID=self.edge_id).data

        # Get Interfaces
        interfaces = deployment.get('modeIfs', None)

        # Locate Deployment Param: testing_interface
        testing_interface = None
        for inter in interfaces:
            if inter['ifName'] == self.testing_interface['interface']:
                testing_interface = inter

        # Get the appliances connected to the LAN Interface
        appliances = testing_interface.get('applianceIPs', None)

        # Set the Deployment Param: testing_fw_zone for testing_interface
        for appliance in appliances:
            if appliance['label'] == self.testing_interface['label']['id'] and self.testing_interface['comment'] in appliance['comment'].lower():
                appliance['zone'] = self.testing_fw_zone['id']

        deployment = json.dumps(deployment)

        response = self.api.post_deployment_data(applianceID=self.edge_id, deploymentData=deployment, timeout=240)

        if self.debug:
            print(response)

        if response.status_code == 200:
            print(response.data)
        else:
            print(response)

    def set_default_fw_zone_for_testing_interface(self):
        """
        Sets Deployment Parameter: self.default_fw_zone for self.testing_interface for FW Zone
        :return: Prints result
        """

        if self.debug:
            print("FW Zone '{} id:{]' for Interface '{}'".format(self.default_fw_zone['name'],
                                                                 self.default_fw_zone['id'],
                                                                 self.testing_interface['interface']))

        # Get Edge's deployment data
        deployment = self.api.get_deployment_data(applianceID=self.edge_id).data

        # Get Interfaces
        interfaces = deployment.get('modeIfs', None)

        # Locate Deployment Param: testing_interface
        testing_interface = None
        for inter in interfaces:
            if inter['ifName'] == self.testing_interface['interface']:
                testing_interface = inter

        # Get the appliances connected to the LAN Interface
        appliances = testing_interface.get('applianceIPs', None)

        # Set the Deployment Param: testing_fw_zone for testing_interface
        for appliance in appliances:
            if appliance['label'] == self.testing_interface['label']['id'] and self.testing_interface['comment'] in appliance['comment'].lower():
                appliance['zone'] = self.default_fw_zone['id']

        deployment = json.dumps(deployment)

        response = self.api.post_deployment_data(applianceID=self.edge_id, deploymentData=deployment, timeout=240)

        if self.debug:
            print(response)

        if response.status_code == 200:
            print(response.data)
        else:
            print(response)

    def is_testing_fw_zone_set_for_testing_interface(self):
        """
        Verifies if Deployment Parameter: self.testing_interface has self.testing_fw_zone has its fw zone

        Appliance > Deployment > Router >   Interface = self.testing_interface['interface']
                                            Label = self.testing_interface['label']
                                            IP/Mask comment = self.testing_interface['comment']

        Looking for above conditions
        :return: bool
        """

        # Check if testing_interface label exists
        if not self.verify_testing_interface_label_exists():
            print('Deployment Param Interface Label:{} with id:{} does not exists. Please add Interface Label and update Deployment Parameters'.format(
                self.testing_interface['label']['name'],
                self.testing_interface['label']['id']
            ))
            exit()

        # Get Edge's deployment data
        deployment = self.api.get_deployment_data(applianceID=self.edge_id).data

        # Get Deployment Param: testing_interface
        interfaces = deployment.get('modeIfs', None)

        # Locate LAN Interface
        testing_interface = None
        for inter in interfaces:
            if inter['ifName'] == self.testing_interface['interface']:
                testing_interface = inter

        # Get the appliances connected to the LAN Interface
        appliances = testing_interface.get('applianceIPs', None)

        # Check if the appliance with matching Deployment Param has self.testing_fw_zone as its FW Zone
        for appliance in appliances:
            if appliance['label'] == self.testing_interface['label']['name'] and \
                    self.testing_interface['comment'] in appliance['comment'].lower():
                if appliance['zone'] == self.testing_fw_zone['id']:
                    return True

        if self.debug:
            print("FW Zone '{} id:{}' is not set for Interface '{}'".format(self.testing_fw_zone['name'],
                                                                            self.testing_fw_zone['id'],
                                                                            self.testing_interface['interface']))
        return False

    def verify_testing_interface_label_exists(self):
        """
        Verifies if Deployment Parameter: self.testing_interface['label'] exists in Deployment config

        :return: bool
        """

        # Get active 'lan' Interface Labels
        labels = self.api.get_interface_labels(type='lan', active=True).data

        try:
            testing_label = labels.get(str(self.testing_interface['label']['id']), None)
            # Check if the testing_label matches Deployment Parameters
            if testing_label['name'] == self.testing_interface['label']['name']:
                return True
            else:
                if self.debug:
                    print("self.testing_interface['label']['name'] = {} does not match. Label id = {} has the name {}".format(
                        self.testing_interface['label']['name'],
                        self.testing_interface['label']['id'],
                        testing_label['name']
                    ))
                return False
        except KeyError:
            if self.debug:
                print("self.testing_interface['label'] {}: id{} does not exists".format(self.testing_interface['label']['name'],
                                                                                        self.testing_interface['label']['id']))
            return False
