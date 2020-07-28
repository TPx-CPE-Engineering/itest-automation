from silverpeak import *
import json
import time
import requests.exceptions

"""
Base Edge template for Silverpeak automation
"""
SP_USERNAME = 'juan.brena'
SP_PASSWORD = '1Maule1!'
SP_SERVER = 'cpesp.lab-sv.telepacific.com'


class SPBaseEdge:
    def __init__(self, edge_id, enterprise_id, ssh_port, auto_operator_login=True):
        self.edge_id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port
        self.api = None
        self.cpe_lan_ip = None
        self.debug = False

        if auto_operator_login:
            self.api = operator_login()

        # Deployment Parameters
        self.DEFAULT_fw_zone = {'name': 'Default',
                                'id': 0}

        self.ONE_fw_zone = {'name': 'ONE',
                            'id': 12}

        self.Voice_label = {'name': 'Voice',
                            'id': '4'}

        self.LAN0_interface = {'interface': 'lan0',
                               'vlan': None,
                               'fw_zone': self.ONE_fw_zone,
                               'label': self.Voice_label,
                               'ip/mask': None,
                               'comment': 'itest'}

        self.RealTime_overlay = {'name': 'RealTime',
                                 'id': 1}

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

    def set_fw_zone_for_interface(self, fw_zone, interface):
        """
        Sets fw_zone as interface's FZ Zone
        :return: Prints API Call result
        """

        if self.debug:
            print("Setting FW Zone '{} id:{]' for Interface '{}'".format(fw_zone['name'],
                                                                         fw_zone['id'],
                                                                         interface['interface']))

        # Avoid setting fw zone if already set
        if self.is_fw_zone_set_for_interface(fw_zone=fw_zone, interface=interface):
            return

        # Get Edge's deployment data
        deployment = self.api.get_deployment_data(applianceID=self.edge_id).data

        # Get Interfaces
        interfaces = deployment.get('modeIfs', None)

        # Locate Deployment Param: testing_interface
        deployment_interface = None
        for inter in interfaces:
            if inter['ifName'] == self.LAN0_interface['interface']:
                deployment_interface = inter

        # Get the appliances connected to the LAN Interface
        appliances = deployment_interface.get('applianceIPs', None)

        # Set the Deployment Param: testing_fw_zone for testing_interface
        for appliance in appliances:
            if appliance['label'] == interface['label']['id'] and interface['comment'] in appliance['comment'].lower():
                appliance['zone'] = fw_zone['id']

        deployment = json.dumps(deployment)

        self.api.post_deployment_data(applianceID=self.edge_id, deploymentData=deployment)
        time.sleep(10)

        # if self.debug:
        #     print(response)

        while True:
            deployment = None
            try:
                deployment = self.api.get_deployment_data(applianceID=self.edge_id).data
            except requests.exceptions.ReadTimeout:
                pass

            if deployment is not None:
                if self.is_fw_zone_set_for_interface(fw_zone=fw_zone, interface=interface):
                    print('FW Zone config applied')
                else:
                    print('Error applying FW Zone config')
                break

            print('Applying FW Zone config...')
            time.sleep(5)

    def is_fw_zone_set_for_interface(self, fw_zone, interface):
        """
        Verifies if interface has fw_zone has its FW Zone

        Appliance > Deployment > Router >   Interface = interface['interface']
                                            Label = interface['label']
                                            IP/Mask comment = interface['comment']

        Looking for above conditions
        :return: bool
        """

        # Check if testing_interface label exists
        if not self.verify_interface_label_exists(interface=interface):
            print('Interface Label:{} with id:{} does not exists. Please add Interface Label and update Deployment Parameters'.format(
                interface['label']['name'],
                interface['label']['id']
            ))
            exit()

        # Get Edge's deployment data
        deployment = self.api.get_deployment_data(applianceID=self.edge_id).data

        # Get Deployment Param: testing_interface
        interfaces = deployment.get('modeIfs', None)

        # Locate LAN Interface
        deployment_interface = None
        for inter in interfaces:
            if inter['ifName'] == self.LAN0_interface['interface']:
                deployment_interface = inter

        # Get the appliances connected to the LAN Interface
        appliances = deployment_interface.get('applianceIPs', None)

        # Check if the appliance with matching Deployment Param has self.testing_fw_zone as its FW Zone
        for appliance in appliances:
            if appliance['label'] == interface['label']['id'] and \
                    interface['comment'].lower() in appliance['comment'].lower():
                if appliance['zone'] == fw_zone['id']:
                    return True

        if self.debug:
            print("FW Zone '{} id:{}' is not set for Interface '{}'".format(fw_zone['name'],
                                                                            fw_zone['id'],
                                                                            interface['interface']))
        return False

    def verify_interface_label_exists(self, interface):
        """
        Verifies if Interface label exists in Deployment config

        :return: bool
        """

        # Get active 'lan' Interface Labels
        labels = self.api.get_interface_labels(type='lan', active=True).data

        try:
            label = labels.get(str(interface['label']['id']), None)
            # Check if the testing_label matches Deployment Parameters
            if label['name'] == interface['label']['name']:
                return True
            else:
                if self.debug:
                    print("Label = {} does not match. Label id = {} has the Label name {}".format(
                        interface['label']['name'],
                        interface['label']['id'],
                        label['name']
                    ))
                return False
        except KeyError:
            if self.debug:
                print("Label {}: id{} does not exists".format(interface['label']['name'], interface['label']['id']))
            return False

    def is_fw_zone_set_for_overlay(self, fw_zone, overlay):
        """
        Verifies if FW Zone is set for Overlay
        :param fw_zone: FW ZONE id
        :param overlay: Overlay id
        :return: bool
        """

        overlay = self.api.get_overlay_data(overlayID=overlay['id']).data

        if overlay['zoneId'] == fw_zone['id']:
            return True
        else:
            return False

    def set_fw_zone_for_overlay(self, fw_zone, overlay):
        """
        Sets fw zone as Overlay's FW Zone
        :param fw_zone: FW Zone to set to
        :param overlay: Overlay
        :return: None
        """

        # Get overlays
        overlays = self.api.get_overlay_regions_data().data

        # Verify you are modifying the correct Overlay
        if not overlays['1']['0']['name'] == overlay['name']:
            print("{} is not Priority #1 in Overlays".format(overlay['name']))
            return

        # Update overlay fw zone id
        overlays['1']['0']['zoneId'] = fw_zone['id']
        overlays = json.dumps(overlays)

        response = self.api.put_overlay_regions_data(overlayRegionData=overlays)

        if not response.status_code == 204:
            print(response)

    def reset_port_flow(self, port):
        """
        Reset flows queried by port
        :return: None
        """
        # Get flows queried by port
        port_query = {'ip1': '',
                      'mask1': '',
                      'port1': port,
                      'ip2': '',
                      'mask2': '',
                      'port2': port,
                      'ipEitherFlag': True,
                      'portEitherFlag': True,
                      'application': '',
                      'applicationGroup': '',
                      'protocol': '',
                      'vlan': '',
                      'dscp': 'any',
                      'overlays': '',
                      'transport': '',
                      'services': '',
                      'zone1': '',
                      'zone2': '',
                      'zoneEither': 'any',
                      'filter': 'all',
                      'edgeHA': False,
                      'builtIn': False,
                      'uptime': 'anytime|term',
                      'bytes': 'last5m',
                      'duration': 'any',
                      'maxFlows': '10000'
                      }

        # Get flow IDs to reset
        flows = self.api.get_flows(applianceID=self.edge_id, flowsQuery=port_query).data

        port_flow_ids = []
        for flow in flows['flows']:
            # flow is a list
            # first item in flow will be the flow id
            # put them all in a list to reset them
            port_flow_ids.append(flow[0])

        flow_reset_data = {'spIds': port_flow_ids}
        flow_reset_data = json.dumps(flow_reset_data)

        response = self.api.post_flow_reset(applianceID=self.edge_id, flowResetData=flow_reset_data)
        if response.status_code == 204:
            print({'error reset port flows': None})
        else:
            print({'error reset port flows': response.error})


def operator_login():
    sp = Silverpeak(user=SP_USERNAME, user_pass=SP_PASSWORD, sp_server=SP_SERVER, disable_warnings=True, auto_login=True)

    if not sp.login_result.ok:
        print(sp.login_result)
        exit()

    return sp
