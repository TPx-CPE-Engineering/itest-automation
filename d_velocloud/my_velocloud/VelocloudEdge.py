from my_velocloud import Globals
from my_velocloud.VcoRequestManager import VcoRequestManager, ApiException
import json
import time
from bs4 import BeautifulSoup


class VeloCloudEdge(object):
    def __init__(self, edge_id, enterprise_id, cpe_ssh_port=None, authenticate=True, hostname=Globals.VC_SERVER,
                 verify_ssl=False, username=Globals.VC_USERNAME, password=Globals.VC_PASSWORD, is_operator=True):
        self.id = int(edge_id)
        self.enterprise_id = int(enterprise_id)
        if cpe_ssh_port:
            self.cpe_ssh_port = int(cpe_ssh_port)
        self.voice_segment_name = Globals.VOICE_SEGMENT_NAME
        self.client = VcoRequestManager(hostname=hostname, verify_ssl=verify_ssl)
        self.live_mode_token = None

        if authenticate:
            self.client.authenticate(username=username, password=password, is_operator=is_operator)

    def get_vlan_id_from_vlan_name(self, vlan_name:str):
        device_settings_module = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for network in device_settings_module['data']['lan']['networks']:
            if network['name'].lower() == vlan_name.lower():
                return {"vlan name": network['name'],
                        "vlan id": network['vlanId']}

    def get_active_device_serial_number(self):
        edge_info = self.get_edge()

        # Depending on the device family, we either collect the first or last 3 characters
        models_to_get_last_three_serial_numbers = ['EDGE5X0', 'EDGE8X0']

        response = {"serial number": None,
                    "switch serial number": None}

        if edge_info['deviceFamily'] in models_to_get_last_three_serial_numbers:
            response["serial number"] = edge_info["serialNumber"]
            response["switch serial number"] = edge_info["serialNumber"][-3:]
            return response
        else:
            response["serial number"] = edge_info["serialNumber"]
            response["switch serial number"] = edge_info["serialNumber"][:3]
            return response

    def get_ha_device_serial_number(self):
        edge_info = self.get_edge()

        # Depending on the device family, we either collect the first or last 3 characters
        models_to_get_last_three_serial_numbers = ['EDGE5X0', 'EDGE8X0']

        response = {"ha serial number": None,
                    "switch serial number": None}

        if edge_info['deviceFamily'] in models_to_get_last_three_serial_numbers:
            response["ha serial number"] = edge_info["haSerialNumber"]
            response["switch serial number"] = edge_info["haSerialNumber"][-3:]
            return response
        else:
            response["ha serial number"] = edge_info["haSerialNumber"]
            response["switch serial number"] = edge_info["haSerialNumber"][:3]
            return response

    def get_edge(self):
        method = '/edge/getEdge/'
        params = {"id": self.id,
                  "enterpriseId": self.enterprise_id}

        response = self.client.call_api(method=method, params=params)
        return response

    def set_live_mode_token(self):
        """
        Set Live Mode Token

        Token is needed for Live Mode API Calls
        :return: None
        """

        method = '/liveMode/enterLiveMode'
        params = {'edgeId': self.id,
                  'enterpriseId': self.enterprise_id}

        response = self.client.call_api(method=method, params=params)
        self.live_mode_token = response['token']

    def get_edge_configuration_stack(self) -> list:
        """
        Get an edge's complete configuration profile, with all modules included
        :return: Edge's configuration stack as a list.
        """

        method = '/edge/getEdgeConfigurationStack/'
        params = {"edgeId": self.id,
                  "enterpriseId": self.enterprise_id}

        response = self.client.call_api(method=method, params=params)
        return response

    def get_edge_specific_profile(self) -> dict:
        """
        Get Edge's edge specific profile
        :return: Edge specific profile
        """

        edge_configuration_stack = self.get_edge_configuration_stack()
        # Index 0 contains edge specific profile
        return edge_configuration_stack[0]

    def get_enterprise_profile(self) -> dict:
        """
        Get Edge's enterprise profile
        :return: Edge's enterprise profile
        """

        edge_configuration_stack = self.get_edge_configuration_stack()
        # Index 1 contains edge specific profile
        return edge_configuration_stack[1]

    def get_module_from_edge_specific_profile(self, module_name: str) -> dict:
        """
        Get a specific module from Edge's edge specific profile
        :param module_name: Module name that you want to retrieve
        :return: An edge specific module
        """

        if not (module_name == 'controlPlane' or
                module_name == 'deviceSettings' or
                module_name == 'firewall' or
                module_name == 'QOS' or
                module_name == 'WAN'):
            raise ApiException('Module name error. Module is not one of the following: \'controlPlane\', '
                               '\'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'. '
                               'Your selection: {}'.format(module_name))

        edge_specific_profile = self.get_edge_specific_profile()

        for module in edge_specific_profile['modules']:
            if module['name'] == module_name:
                return module

    def get_module_from_enterprise_profile(self, module_name: str) -> dict:
        """
        Get a specific module from Edge's enterprise profile
        :param module_name: Module name that you want to retrieve
        :return: An enterprise profile module
        """

        if not (module_name == 'controlPlane' or
                module_name == 'deviceSettings' or
                module_name == 'firewall' or
                module_name == 'QOS' or
                module_name == 'WAN'):
            raise ApiException('Module name error. Module is not one of the following: \'controlPlane\', '
                               '\'devicesSettings\', \'firewall\', \'QOS\', \'WAN\'. '
                               'Your selection: {}'.format(module_name))

        enterprise_profile = self.get_enterprise_profile()

        for module in enterprise_profile['modules']:
            if module['name'] == module_name:
                return module

    def get_device_settings_segments(self) -> list:
        """
        Get all Edge' device settings segments
        :return: All Edge's device settings segments
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        edges_segments = []

        for segment in device_settings['data']['segments']:
            edges_segments.append(segment)

        return edges_segments

    def get_a_device_settings_segment(self, segment_name) -> dict:
        """
        Get a specific Edge segment from device settings
        :param segment_name: Name of segment you want to get
        :return: Edge device settings segment
        """

        device_settings_segments = self.get_device_settings_segments()

        for segment in device_settings_segments:
            if segment['segment']['name'] == segment_name:
                return segment

        return {}

    def get_all_configure_vlans(self) -> list:
        """
        Get All Configure VLANS information from an Edge Device Settings
        :return: List of Edge VLANS
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        return device_settings['data']['lan']['networks']

    def update_configuration_module(self, module):
        """
        Update Edge Configuration Module
        :param module: Module you wish to update
        :return: API response
        """

        if module['name'] == 'firewall' or module['name'] == 'QOS' or module['name'] == 'WAN':
            # Firewall Module doesn't have 'refs' key
            # WAN Module doesn't have 'refs' key
            # QOS Module doesn't have 'refs' key either
            update = {'data': module['data'],
                      'description': None,
                      'name': module['name']}
        else:
            update = {'data': module['data'],
                      'refs': module['refs'],
                      'description': None,
                      'name': module['name']}

        params = {'id': module['id'],
                  '_update': update,
                  'returnData': False,
                  'enterpriseId': self.enterprise_id,
                  'isAsync': True}

        method = 'configuration/updateConfigurationModule'

        return self.client.call_api(method, params)

    def get_html_results_from_action_key(self, action_key):
        """
        Get HTML Results based on Live Mode action key
        :param action_key: Live Mode action key
        :return: None
        """

        method = "liveMode/readLiveData"
        params = {"token": self.live_mode_token}

        action = None
        status = None
        dump_complete = False

        # Continue to get live data until you obtain the data from the action key
        while not dump_complete:
            time.sleep(0.5)
            print('Getting live data...')
            # We're looking for a status value greater than 1 as a cue that the remote procedure has
            # completed.
            #
            # Status enum is:
            #   0: PENDING
            #   1: NOTIFIED (i.e. Edge has acknowledge its receipt of the action)
            #   2: COMPLETE
            #   3: ERROR
            #   4: TIMED OUT

            live_data = self.client.call_api(method=method, params=params)

            # Check if Live Action is Active, after some time it becomes inactive
            # If so, get another Live Mode token
            try:
                is_live_mode_active = live_data.get("status", {}).get("isActive", None)
                if not is_live_mode_active:
                    # print('Live Mode is Not Active')
                    self.set_live_mode_token()
                    time.sleep(10)
                    continue
            except AttributeError:
                continue

            try:
                all_action_data = live_data.get("data", {}).get("liveAction", {}).get("data", [])
            except AttributeError:
                continue

            actions_matching_key = [a for a in all_action_data if a["data"]["actionId"] == action_key]
            if len(actions_matching_key) > 0:
                action = actions_matching_key[0]
                status = action["data"]["status"]
            else:
                status = 0

            dump_complete = status > 1

        if status == 2:
            diagnostics_results = action["data"].get("results", [])
            soup = BeautifulSoup(diagnostics_results[0]['results']['output'], "html.parser")
            return soup.get_text()
        else:
            raise ApiException(f"Encountered API error in call to '{method}'")

    def exit_live_mode(self):
        """
        Exit Live Mode gracefully
        :return: <str> Successful message: "Live Mode exited successfully"
        """

        method = 'liveMode/exitLiveMode'
        params = {'edgeId': self.id,
                  'enterpriseId': self.enterprise_id}

        return self.client.call_api(method=method, params=params)

    @staticmethod
    def print_as_json(text):
        """
        Prints text as json

        To be used when trying to insert text into JSON beautifier
        :param text: Text to be printed in json format
        :return: None
        """

        print(json.dumps(text))

    def restore_config_from_filename(self, filename):
        """
        Restore an Edge's module name config based on filename
        :param filename: Filename to read from
        :return: API response
        """

        with open(filename) as json_file:
            config_data = json.load(json_file)
            return self.update_configuration_module(module=config_data)

    @staticmethod
    def delete_filename(filename):
        """
        Delete a filename
        :param filename: Name of filename to delete
        :return: None
        """
        import os

        if os.path.isfile(filename):
            os.remove(filename)

    def get_vlan(self, vlan_id) -> dict:
        """
        Get Edge VLAN
        :param vlan_id: ID of VLAN you want to retrieve
        :return: Edge's VLAN if vlan_id exists

        Return example:
        {
          "vlanId": 1,
          "name": "Corporate",
          "segmentId": 0,
          "disabled": false,
          "advertise": true,
          "cost": 10,
          "cidrIp": "192.168.184.1",
          "cidrPrefix": 24,
          "netmask": "255.255.255.0",
          "dhcp": {
            "enabled": true,
            "leaseTimeSeconds": 86400,
            "options": []
          },
          "staticReserved": 10,
          "baseDhcpAddr": 13,
          "numDhcpAddr": 242,
          "multicast": {
            "igmp": {
              "enabled": false,
              "type": "IGMP_V2"
            },
            "pim": {
              "enabled": false,
              "type": "PIM_SM"
            },
            "pimKeepAliveTimerSeconds": null,
            "pimPruneIntervalSeconds": null,
            "igmpHostQueryIntervalSeconds": null,
            "igmpMaxQueryResponse": null
          },
          "ospf": {
            "enabled": true,
            "area": 0,
            "passiveInterface": true,
            "override": false
          },
          "pingResponse": true,
          "fixedIp": [
            {
              "macAddress": "00:0c:29:3d:d6:60",
              "lanIp": "192.168.184.23",
              "description": "Private DNS Server"
            }
          ],
          "interfaces": [
            "GE2"
          ]
        }
        """
        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for network in device_settings['data']['lan']['networks']:
            if network['vlanId'] == vlan_id:
                return network

        return {}

    def save_module_to_restore(self, module_name, path, filename, enterprise_level=False):
        """
        Save a module settings to a file. This file can later be used to reformat Edge.

        :param module_name: Name of module to save
        :param path: Path where the file will be save
        :param filename: Name of the file
        :param enterprise_level: Module level, either on Edge or Enterprise, default False
        :return: None
        """

        if enterprise_level:
            # Module wishing to save exists in the enterprise level
            module = self.get_module_from_enterprise_profile(module_name=module_name)
        else:
            module = self.get_module_from_edge_specific_profile(module_name=module_name)

        file = path + filename + ".json"

        try:
            with open(file, 'w') as outfile:
                json.dump(module, outfile)
                outfile.close()
        except Exception as err:
            print({'error': err})

    def restore_module(self, path, filename):
        file = path + filename + '.json'
        file = open(file, "r")

        module_as_str = file.read()
        module = json.loads(module_as_str)

        self.update_configuration_module(module=module)

    def add_firewall_rule_to_segment(self, firewall_rule, segment_name):
        """
        Add a Firewall rule to an Edges Segment on Edge Specific Profile
        :param firewall_rule: Firewall rule to add
        :param segment_name: Name of segment to add the firewall rule to
        :return: API Response
        """
        firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Locate segment
        segment = None
        for seg in firewall['data']['segments']:
            if seg['segment']['name'] == segment_name:
                segment = seg

        # Check if segment was not found
        if segment is None:
            raise ValueError(f"Segment: '{segment_name}' was not found.")

        # Append rule to segment
        segment['outbound'].append(firewall_rule)

        # Push change
        return self.update_configuration_module(module=firewall)

    def remove_firewall_rule_from_segment(self, firewall_rule_name, segment_name):
        """
        Remove a Firewall rule from an Edge's Segment on Edge Specific Profile
        :param firewall_rule_name: Name of firewall rule to remove
        :param segment_name: Name of segment to remove the firewall rule from
        :return: API Response
        """

        firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        # Locate segment
        segment = None
        for seg in firewall['data']['segments']:
            if seg['segment']['name'] == segment_name:
                segment = seg

        # Check if segment was not found
        if segment is None:
            raise ValueError(f"Segment: '{segment_name}' was not found.")

        # Locate rule
        for firewall_rule in segment['outbound']:
            if firewall_rule['name'] == firewall_rule_name:
                segment['outbound'].remove(firewall_rule)

        # Push change
        return self.update_configuration_module(module=firewall)

    def set_snmp_v2c_settings(self):
        """
        Sets SNMP Settings for testing Firewall 4.18 & Firewall 4.16

        Versions Enabled: v2c
        Port: 161
        SNMP v2c Config
        Community: tpc1n0c
        Allowed IPs: Any
        :return: API Response
        """

        # Get Device Settings
        device_settings_modules = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Configure SNMP Settings
        snmp = {
            'port': 161,
            'snmpv2c': {
                'enabled': True,
                'community': 'tpc1n0c',
                'allowedIp': []
            },
            'snmpv3': {
                'enabled': False,
                'users': [
                    {
                        'name': 'admin',
                        'passphrase': 'MattKenseth1!',
                        'authAlg': 'MD5',
                        'privacy': False,
                        'encrAlg': 'DES'
                    }
                ],
            },
        }

        # Add snmp to device settings
        device_settings_modules['data']['snmp'] = snmp

        # Push API command
        return self.update_configuration_module(module=device_settings_modules)

    def set_snmp_access_to_deny_all(self):
        """
        Sets the Edge's Firewall SNMP Access to 'Deny All'

        SNMP Access can be found within the Edge's Firewall tab
        """

        # Get Edge's Edge Specific Firewall module
        firewall_module = self.get_module_from_edge_specific_profile(module_name='firewall')

        firewall_module['data']['services']['snmp']['enabled'] = False

        return self.update_configuration_module(module=firewall_module)

    def get_cpe_lan_ip(self) -> str:
        """
        Gets the LAN IP of the CPE behind the edge

        Searches through the edge's inbound firewall rules for a rule that has the following conditions:
        1. rule's name has the keyword 'itest' in it
        2. rule's protocol is 'TCP'
        3. rule's WAN Ports equals global SSH_PORT
        4. rule's LAN Port is 22
        Once it finds such rule, it returns the rule's LAN IP which will be the CPE's IP
        :return: LAN IP
        """

        firewall = self.get_module_from_edge_specific_profile(module_name='firewall')

        tcp = 6
        lan_port = 22

        for rule in firewall['data']['inbound']:
            if 'itest' in rule['name'].lower() and \
                    rule['match']['proto'] == tcp and \
                    rule['match']['dport_high'] == self.cpe_ssh_port and \
                    rule['match']['dport_low'] == self.cpe_ssh_port and \
                    rule['action']['nat']['lan_port'] == lan_port:
                return rule['action']['nat']['lan_ip']

        raise ValueError("Cannot find CPE's LAN IP by looking through firewall rules.")

    def get_enterprise_gateway_handoff(self):

        method = '/enterprise/getEnterpriseGatewayHandoff'
        params = {"enterpriseId": self.enterprise_id}

        return self.client.call_api(method=method, params=params)

    def get_enterprise_edge_info(self, specific_key=None):
        method = 'enterprise/getEnterpriseEdges'
        params = {
            "edgeIds": [self.id],
            "enterpriseId": self.enterprise_id,
        }

        edge_information = self.client.call_api(method=method, params=params)

        if specific_key is None:
            return edge_information

        specific_value = edge_information[0].get(specific_key)
        return {specific_key: specific_value}

    def get_enterprise_events(self, start_interval):
        method = 'event/getEnterpriseEvents'
        params = {
            "enterpriseId": self.enterprise_id,
            "interval": {
                "start": int(start_interval),
            },
            "edgeId": self.id
        }

        return self.client.call_api(method=method, params=params)

    def get_active_wan_interfaces(self):
        # Get WAN Module from Edge Specific Profile
        wan_data = self.get_module_from_edge_specific_profile(module_name='WAN')

        # Get active WAN interfaces
        active_wan_interfaces = []

        # Iterate over each network to get interface associations
        for network in wan_data['data']['networks']:
            interface = network['interface']
            ip_address = network['ipAddress']
            wan_interface = {'interface': interface, 'ip address': ip_address}
            active_wan_interfaces.append(wan_interface)

        return active_wan_interfaces

    def add_business_policy_rule_to_prefer_interface(self, affected_interface, segment_name='Global Segment'):

        # Get the current QoS Module
        qos_module = self.get_module_from_edge_specific_profile(module_name='QOS')

        # Check to see if the segment exists.
        segment_to_update = None

        if segment_name == "Global Segment":
            segment_id = 0
            segment_type = "REGULAR"
            # segmentLogicalId remains the same between edges
            segment_logical_id = "5dcc72f7-ed23-4bb1-967a-c5269d651a05"
        elif segment_name == "Voice Segment":
            segment_id = 3
            segment_type = "REGULAR"
            # segmentLogicalId remains the same between edges
            segment_logical_id = "06c6e557-6d8c-4836-8015-dfc2ffe7de8b"
        else :
            return 'Segment [%s] does not exist' % segment_name
            # TODO: Other segments

        for segment in qos_module['data']['segments']:
            if segment['segment']['name'] == segment_name:
                segment_to_update = segment

        # If the segment does not exist, add the segment itself, as well as the rule
        if segment_to_update is None:
            # Construct the segment data
            segment_to_update = {
                "segment": {
                    "segmentId": segment_id,
                    "name": segment_name,
                    "type": segment_type,
                    "segmentLogicalId": segment_logical_id
                },
                "rules": [
                    {
                        "name": "[AUTOMATION] Prefer " + affected_interface,
                        "match": {
                            "appid": -1,
                            "classid": -1,
                            "dscp": -1,
                            "sip": "any",
                            "sport_high": -1,
                            "sport_low": -1,
                            "ssm": "255.255.255.255",
                            "svlan": -1,
                            "os_version": -1,
                            "hostname": "",
                            "dip": "any",
                            "dport_low": -1,
                            "dport_high": -1,
                            "dsm": "255.255.255.255",
                            "dvlan": -1,
                            "proto": -1,
                            "s_rule_type": "prefix",
                            "d_rule_type": "prefix"
                        },
                        "action": {
                            "routeType": "edge2Any",
                            "allowConditionalBh": False,
                            "userDisableConditionalBh": False,
                            "edge2EdgeRouteAction": {
                                "interface": affected_interface,
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "gateway",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": affected_interface,
                                "linkCosLogicalId": "",
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": ""
                            },
                            "edge2DataCenterRouteAction": {
                                "interface": affected_interface,
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "auto",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": affected_interface,
                                "linkCosLogicalId": "",
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": ""
                            },
                            "edge2CloudRouteAction": {
                                "interface": affected_interface,
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "gateway",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": affected_interface,
                                "linkCosLogicalId": None,
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": None
                            },
                            "QoS": {
                                "type": "transactional",
                                "rxScheduler": {
                                    "bandwidth": -1,
                                    "bandwidthCapPct": -1,
                                    "queueLen": -1,
                                    "burst": -1,
                                    "latency": -1,
                                    "priority": "normal"
                                },
                                "txScheduler": {
                                    "bandwidth": -1,
                                    "bandwidthCapPct": -1,
                                    "queueLen": -1,
                                    "burst": -1,
                                    "latency": -1,
                                    "priority": "normal"
                                }
                            },
                            "sla": {
                                "latencyMs": "0",
                                "lossPct": "0.0",
                                "jitterMs": "0"
                            },
                            "nat": {
                                "sourceIp": "no",
                                "destIp": "no"
                            }
                        }
                    }
                ],
                "webProxy": {
                    "providers": []
                }
            }

            # Append to the global segment
            qos_module['data']['segments'].append(segment_to_update)

        # Else the segment already exists, add the rule to the existing segment
        else:
            # we append the rule to the already existing data
            rule = {
                "name": "[AUTOMATION] Prefer " + affected_interface,
                "match": {
                    "appid": -1,
                    "classid": -1,
                    "dscp": -1,
                    "sip": "any",
                    "sport_high": -1,
                    "sport_low": -1,
                    "ssm": "255.255.255.255",
                    "svlan": -1,
                    "os_version": -1,
                    "hostname": "",
                    "dip": "any",
                    "dport_low": -1,
                    "dport_high": -1,
                    "dsm": "255.255.255.255",
                    "dvlan": -1,
                    "proto": -1,
                    "s_rule_type": "prefix",
                    "d_rule_type": "prefix"
                },
                "action": {
                    "routeType": "edge2Any",
                    "allowConditionalBh": False,
                    "userDisableConditionalBh": False,
                    "edge2EdgeRouteAction": {
                        "interface": affected_interface,
                        "subinterfaceId": -1,
                        "linkInternalLogicalId": "auto",
                        "linkPolicy": "fixed",
                        "routeCfg": {},
                        "routePolicy": "gateway",
                        "serviceGroup": "ALL",
                        "vlanId": -1,
                        "wanlink": affected_interface,
                        "linkCosLogicalId": None,
                        "linkOuterDscpTag": "CS0",
                        "linkInnerDscpTag": None
                    },
                    "edge2DataCenterRouteAction": {
                        "interface": affected_interface,
                        "subinterfaceId": -1,
                        "linkInternalLogicalId": "auto",
                        "linkPolicy": "fixed",
                        "routeCfg": {},
                        "routePolicy": "auto",
                        "serviceGroup": "ALL",
                        "vlanId": -1,
                        "wanlink": affected_interface,
                        "linkCosLogicalId": None,
                        "linkOuterDscpTag": "CS0",
                        "linkInnerDscpTag": None
                    },
                    "edge2CloudRouteAction": {
                        "interface": affected_interface,
                        "subinterfaceId": -1,
                        "linkInternalLogicalId": "auto",
                        "linkPolicy": "fixed",
                        "routeCfg": {},
                        "routePolicy": "gateway",
                        "serviceGroup": "ALL",
                        "vlanId": -1,
                        "wanlink": affected_interface,
                        "linkCosLogicalId": None,
                        "linkOuterDscpTag": "CS0",
                        "linkInnerDscpTag": None
                    },
                    "QoS": {
                        "type": "transactional",
                        "rxScheduler": {
                            "bandwidth": -1,
                            "bandwidthCapPct": -1,
                            "queueLen": -1,
                            "burst": -1,
                            "latency": -1,
                            "priority": "normal"
                        },
                        "txScheduler": {
                            "bandwidth": -1,
                            "bandwidthCapPct": -1,
                            "queueLen": -1,
                            "burst": -1,
                            "latency": -1,
                            "priority": "normal"
                        }
                    },
                    "sla": {
                        "latencyMs": "0",
                        "lossPct": "0.0",
                        "jitterMs": "0"
                    },
                    "nat": {
                        "sourceIp": "no",
                        "destIp": "no"
                    }
                }
            }
            segment_to_update['rules'].append(rule)

        qos_module['metadata']['override'] = True

        # Update the VeloCloud Edge config module to prefer WAN 1
        update_business_policy = self.update_configuration_module(module=qos_module)

    def remove_business_policy_rule_from_preferred_interface(self, affected_interface, segment_name='Global Segment'):
        # Get the current QoS Module
        qos_module = self.get_module_from_edge_specific_profile(module_name='QOS')

        # Check to see if the segment exists.
        segment_to_update = None

        for segment in qos_module['data']['segments']:
            if segment['segment']['name'] == segment_name:
                segment_to_update = segment

        # Get Global Segment rules
        segment_rules = segment_to_update['rules']

        for segment_rule in segment_rules:
            if segment_rule['name'] == "[AUTOMATION] Prefer " + affected_interface:
                segment_rules = segment_rules.remove(segment_rule)
            else:
                pass

        # Update the VeloCloud Edge config module to remove the rule from the segment
        update_business_policy = self.update_configuration_module(module=qos_module)

    def remove_all_business_policy_rules(self):
        # Get the current QoS Module
        qos_module = self.get_module_from_edge_specific_profile(module_name='QOS')

        # Clear out ALL segments
        qos_module['data']['segments'] = []

        # Update the VeloCloud Edge config module to removes the rule from the segments
        update_business_policy = self.update_configuration_module(module=qos_module)

    def remote_diagnostics_flush_flows(self, src_ip:str = None, dst_ip:str = None):
        """
        Execute a live action to flush the flows for the edge

        Flush the flow table, causing user traffic to be re-classified. Use source and destination IP address filters
        to flush specific flows.
        :param src_ip: Str source ip to flush specific flow
        :param dst_ip: Str destination ip to flush specific flow
        :return: Str of flush flow action result
        """

        if self.live_mode_token is None:
            self.set_live_mode_token()

        # parameter = {
        #     'src_ip': src_ip,
        #     'dst_ip': dst_ip
        # }

        parameter = "{\"src_ip\":\"\",\"dst_ip\":\"\"}"

        method = 'liveMode/requestLiveActions'
        params = {
            "actions": [
                {
                    "action": "runDiagnostics",
                    "parameters": {
                        "tests": [
                            {
                                "name": "FLUSH_FLOWS",
                                "parameters": [
                                    parameter
                                ]
                            }
                        ]
                    }
                }
            ],
            "token": self.live_mode_token
        }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        print(self.get_html_results_from_action_key(action_key=action_key))

        # Exit live mode gracefully
        self.exit_live_mode()


# Class for BGP Testing
class BGPVeloCloudEdge(VeloCloudEdge):

    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

        # Default Values for BGP Testing
        self.default_bgp_segment_name = 'Global Segment'
        self.default_bgp_segment = self.get_a_device_settings_segment(segment_name=self.default_bgp_segment_name)

    def enable_bgp_on_enterprise_segment(self, segment_name='Global Segment'):
        """
        Enable BGP on Enterprise's given segment
        :param segment_name: Segment name you want to enable BGP on
        :return: None
        """

        device_settings = self.get_module_from_enterprise_profile(module_name='deviceSettings')

        # Find the segment to enable BGP on
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Enable bgp
                segment['bgp']['enabled'] = True

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def disable_bgp_on_enterprise_segment(self, segment_name='Global Segment'):
        """
        Disable BGP on Enterprise's given segment
        :param segment_name: Segment name you want to enable BGP on
        :return: None
        """

        device_settings = self.get_module_from_enterprise_profile(module_name='deviceSettings')

        # Find the segment to disable BGP on
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Disable bgp
                segment['bgp']['enabled'] = False

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def disable_bgp_edge_override_on_edge_segment(self, segment_name='Global Segment'):
        """
        Disable BGP Edge Override on Edge's segment
        :param segment_name: Segment name to disable BGP on. Default 'Global Segment'
        :return: None
        """

        # Get Device Settings
        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Update BGP on given segment
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                try:
                    del segment['bgp']
                except KeyError:
                    pass

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def overwrite_bgp_neighbors(self, neighbor_ip, neighbor_asn, segment_name='Global Segment'):
        """
        Overwrite a BGP Neighbor on Edge through Edge Override

        Old BGP Neighbors will be deleted
        :param segment_name: Name of Segment
        :param neighbor_ip: IP of BGP Neighbor to add
        :param neighbor_asn: ASN of BGP Neighbor to add
        :return: None
        """

        bgp_data = {
              "enabled": True,
              "routerId": None,
              "ASN": "65535",
              "networks": [],
              "neighbors": [
                {
                  "neighborIp": neighbor_ip,
                  "neighborAS": neighbor_asn,
                  "inboundFilter": {
                    "ids": []
                  },
                  "outboundFilter": {
                    "ids": []
                  }
                }
              ],
              "overlayPrefix": True,
              "disableASPathCarryOver": True,
              "uplinkCommunity": None,
              "connectedRoutes": True,
              "propagateUplink": False,
              "ospf": {
                "enabled": True,
                "metric": 20
              },
              "defaultRoute": {
                "enabled": False,
                "advertise": "CONDITIONAL"
              },
              "asn": None,
              "isEdge": True,
              "filters": [],
              "override": True
            }

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Update BGP on given segment
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                segment['bgp'] = bgp_data

        response = self.update_configuration_module(module=device_settings)
        print(response)

    def get_vlan_ip_address_from_segment(self, segment_name='Global Segment') -> str:
        """
        Get VLAN IP Address from segment
        :param segment_name: Segment you want to retrieve VLAN IP Address from
        :return: IP Address
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        segment = self.get_a_device_settings_segment(segment_name=segment_name)
        segment_id = segment['segment']['segmentId']

        # Find VLAN
        for network in device_settings['data']['lan']['networks']:
            if network['segmentId'] == segment_id:
                return network['cidrIp']

    def get_new_bgp_neighbor_ip(self) -> str:
        """
        Get New BGP Neighbor IP taken from VLAN (that is on Global Segment) + 1
        :return:
        """
        from ipaddress import ip_address

        # Get VLAN IP
        ip = ip_address(address=self.get_vlan_ip_address_from_segment(segment_name='Global Segment'))
        # Increase VLAN IP address by 1 to set neighbor
        return str(ip + 1)

    def get_bgp_summary(self):
        """
        Show the existing BGP neighbor and received routes
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_SUM",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_neighbor_advertised_routes(self, segment_id, neighbor_ip):
        """
        Get the BGP routes advertised to a neighbor
        :param segment_id: Segment ID
        :param neighbor_ip: Neighbor IP
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_NBR_AD",
                            "parameters": [
                                f"{{\"segment\":\"{segment_id}\", \"nbr_ip\":\"{neighbor_ip}\"}}"
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_bgp_neighbor_received_routes(self, segment_id, neighbor_ip):
        """
        Get all the BGP routes learned from a neighbor before filters
        :param segment_id: Segment ID
        :param neighbor_ip: Neighbor IP
        :return: None
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_BGP_NBR_RCV",
                            "parameters": [
                                f"{{\"segment\":\"{segment_id}\", \"nbr_ip\":\"{neighbor_ip}\"}}"
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def enable_md5_on_bgp_neighbor(self, neighbor_ip, md5_password, segment_name='Global Segment'):
        """
        Enable MD5 for specific BGP Neighbor on an Edge Segment
        :param segment_name: Name of Segment to look in, default 'Global Segment'
        :param neighbor_ip: IP of Neighbor to enable MD5 on
        :param md5_password: MD5 password you wish to set
        :return: API response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Look for the segment, and search through BGP neighbors within segment to find the right neighbor
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Now look for BGP Neighbor
                for neighbor in segment['bgp']['neighbors']:
                    if neighbor['neighborIp'] == neighbor_ip:
                        neighbor['enableMd5'] = True
                        neighbor['md5Password'] = md5_password

        return self.update_configuration_module(module=device_settings)

    def disable_md5_on_bgp_neighbor(self, neighbor_ip, segment_name='Global Segment'):
        """
        Disable MD5 for specific BGP Neighbor on an Edge Segment
        :param neighbor_ip: Ip of Neighbor to disable md5 on
        :param segment_name: Name of Segment to look in, default 'Global Segment'
        :return: API response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Look for the segment, and search through its BGP neighbors to find specific neighbor
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Segment Found
                # Now look for BGP Neighbor
                for neighbor in segment['bgp']['neighbors']:
                    if neighbor['neighborIp'] == neighbor_ip:
                        neighbor['enableMd5'] = False
                        neighbor.pop('md5Password', None)

        return self.update_configuration_module(module=device_settings)


# Class for OSPF Testing
class OSPFVeloCloudEdge(VeloCloudEdge):

    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

    def get_vlan_interfaces(self, vlan_id=1):
        """
        Get List of Interfaces that are on a VLAN ID
        :param vlan_id: ID of VLAN you want to retrieve the interfaces from, default VLAN 1
        :return: list of interfaces
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for network in device_settings['data']['lan']['networks']:
            if vlan_id == network['vlanId']:
                return network['interfaces']

        return []

    def get_vlan_ip_address(self, vlan_id=1):
        """
        Get IP Address of a VLAN
        :param vlan_id: ID of VLAN you want to retrieve the IP Address from
        :return: VLAN ID IP Address
        """
        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for network in device_settings['data']['lan']['networks']:
            if network['vlanId'] == vlan_id:
                return network['cidrIp']

    @staticmethod
    def make_ospf_interface_config(interface_name, ip_address):
        """
        Make JSON Config needed to add OSPF Interface
        :param interface_name: Interface you want to change into OSPF Interface, usually 'GE1' or 'GE2'
        :param ip_address: IP Address
        :return: JSON config to add OSPF Interface
        """

        # Old config, no longer the same since update 4.3.1
        # ospf_routed_interface = {
        #                           "name": interface_name,
        #                           "disabled": False,
        #                           "addressing": {
        #                             "type": "STATIC",
        #                             "cidrPrefix": 24,
        #                             "cidrIp": ip_address,
        #                             "netmask": "255.255.255.0",
        #                             "gateway": None,
        #                             "username": None,
        #                             "password": None
        #                           },
        #                           "wanOverlay": "AUTO_DISCOVERED",
        #                           "encryptOverlay": True,
        #                           "radiusAuthentication": {
        #                             "enabled": False,
        #                             "macBypass": []
        #                           },
        #                           "advertise": False,
        #                           "pingResponse": True,
        #                           "natDirect": True,
        #                           "trusted": False,
        #                           "rpf": "SPECIFIC",
        #                           "ospf": {
        #                             "enabled": True,
        #                             "area": [
        #                               0
        #                             ],
        #                             "authentication": False,
        #                             "authId": 0,
        #                             "authPassphrase": "",
        #                             "helloTimer": 10,
        #                             "mode": "BCAST",
        #                             "deadTimer": 40,
        #                             "md5Authentication": False,
        #                             "cost": 1,
        #                             "MTU": 1380,
        #                             "passive": False,
        #                             "inboundRouteLearning": {
        #                               "defaultAction": "LEARN",
        #                               "filters": []
        #                             },
        #                             "outboundRouteAdvertisement": {
        #                               "defaultAction": "ADVERTISE",
        #                               "filters": []
        #                             }
        #                           },
        #                           "multicast": {
        #                             "igmp": {
        #                               "enabled": False,
        #                               "type": "IGMP_V2"
        #                             },
        #                             "pim": {
        #                               "enabled": False,
        #                               "type": "PIM_SM"
        #                             },
        #                             "pimHelloTimerSeconds": None,
        #                             "pimKeepAliveTimerSeconds": None,
        #                             "pimPruneIntervalSeconds": None,
        #                             "igmpHostQueryIntervalSeconds": None,
        #                             "igmpMaxQueryResponse": None
        #                           },
        #                           "vlanId": None,
        #                           "underlayAccounting": True,
        #                           "segmentId": -1,
        #                           "l2": {
        #                             "autonegotiation": True,
        #                             "speed": "100M",
        #                             "duplex": "FULL",
        #                             "MTU": 1500
        #                           },
        #                           "override": True,
        #                           "dhcpServer": {
        #                             "enabled": False,
        #                             "leaseTimeSeconds": 3600,
        #                             "options": [],
        #                             "baseDhcpAddr": "",
        #                             "numDhcpAddr": 0,
        #                             "staticReserved": 10
        #                           }
        #                         }

        ospf_routed_interface = {
                              "name": interface_name,
                              "disableV4": False,
                              "disableV6": True,
                              "overlayPreference": "IPv4",
                              "disabled": False,
                              "addressing": {
                                "type": "STATIC",
                                "cidrPrefix": 24,
                                "cidrIp": ip_address,
                                "netmask": "255.255.255.0",
                                "gateway": None,
                                "username": None,
                                "password": None
                              },
                              "wanOverlay": "DISABLED",
                              "encryptOverlay": True,
                              "radiusAuthentication": {
                                "enabled": False,
                                "macBypass": []
                              },
                              "v6Detail": {
                                "addressing": {
                                  "cidrPrefix": None,
                                  "netmask": None,
                                  "type": "DHCP_STATELESS",
                                  "gateway": None,
                                  "cidrIp": None
                                },
                                "wanOverlay": "DISABLED",
                                "vlanId": None
                              },
                              "advertise": True,
                              "pingResponse": True,
                              "natDirect": True,
                              "trusted": False,
                              "rpf": "SPECIFIC",
                              "ospf": {
                                "enabled": True,
                                "area": [
                                  0
                                ],
                                "authentication": False,
                                "authId": 0,
                                "authPassphrase": "",
                                "helloTimer": 10,
                                "mode": "BCAST",
                                "deadTimer": 40,
                                "enableBfd": False,
                                "md5Authentication": False,
                                "cost": 1,
                                "MTU": 1380,
                                "passive": False,
                                "inboundRouteLearning": {
                                  "defaultAction": "LEARN",
                                  "filters": []
                                },
                                "outboundRouteAdvertisement": {
                                  "defaultAction": "ADVERTISE",
                                  "filters": []
                                }
                              },
                              "multicast": {
                                "igmp": {
                                  "enabled": False,
                                  "type": "IGMP_V2"
                                },
                                "pim": {
                                  "enabled": False,
                                  "type": "PIM_SM"
                                },
                                "pimHelloTimerSeconds": None,
                                "pimKeepAliveTimerSeconds": None,
                                "pimPruneIntervalSeconds": None,
                                "igmpHostQueryIntervalSeconds": None,
                                "igmpMaxQueryResponse": None
                              },
                              "vlanId": None,
                              "underlayAccounting": True,
                              "segmentId": 0,
                              "l2": {
                                "autonegotiation": True,
                                "speed": "100M",
                                "duplex": "FULL",
                                "MTU": 1500,
                                "losDetection": False,
                                "probeInterval": "3"
                              },
                              "override": True,
                              "dhcpServer": {
                                "enabled": False,
                                "leaseTimeSeconds": 3600,
                                "options": [],
                                "baseDhcpAddr": "",
                                "numDhcpAddr": 0,
                                "staticReserved": 10
                              }
                            }

        return ospf_routed_interface

    def get_ospf_interface_config(self, vlan_id=1):
        """
        Get JSON config to add OSPF Interface
        :return: OSPF Interface as JSON config
        """

        # Find list of interfaces on given VLAN
        vlan_interfaces = self.get_vlan_interfaces(vlan_id=vlan_id)
        if len(vlan_interfaces) == 0:
            print({'error': f'No interfaces found on VLAN {vlan_id}'})
            exit()

        # Get IP Address of given VLAN
        vlan_ip_address = self.get_vlan_ip_address(vlan_id=vlan_id)
        if vlan_ip_address is None:
            print({'error': f'No IP Address found for VLAN {vlan_id}'})
            exit()

        # We'll pick the first one in the list
        return self.make_ospf_interface_config(interface_name=vlan_interfaces[0],
                                               ip_address=vlan_ip_address)

    def add_routed_interface(self, interface, vlan_id):
        """
        Add Interface to Edge interfaces
        :param interface: Interface to add
        :return: API Response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for lan_interface in device_settings['data']['routedInterfaces']:
            if lan_interface['name'] == interface['name']:
                print({'error': f"Interface {interface['name']} already active/exists in Edge's interface. "
                                f"Cannot overwrite"})
                exit()

        # Step1. Remove Interface from Edges LAN Interfaces list
        new_lan_interfaces = []
        for lan_interface in device_settings['data']['lan']['interfaces']:
            if lan_interface['name'] == interface['name']:
                continue
            else:
                new_lan_interfaces.append(lan_interface)

        # Set LAN Interfaces to the new LAN Interfaces list (without the interface)
        device_settings['data']['lan']['interfaces'] = new_lan_interfaces

        # Step2. Remove Interface from Edges LAN Networks Interfaces
        lan_networks_without_interface = []
        for network in device_settings['data']['lan']['networks']:
            if network['vlanId'] == vlan_id:
                for inter_ in network['interfaces']:
                    if inter_ == interface['name']:
                        continue
                    else:
                        lan_networks_without_interface.append(inter_)

        # Set LAN Networks without the interface
        for network in device_settings['data']['lan']['networks']:
            if network['vlanId'] == vlan_id:
                network['interfaces'] = lan_networks_without_interface

        # Append interface to Edges interfaces
        """
        Order matters!
        The following should be the order:
        'GE1'
        'GE2'
        .
        .
        .
        'SFP1'
        'SFP2'        
        """
        # TODO create a function that can order the interfaces in the right order

        device_settings['data']['routedInterfaces'].insert(0, interface)

        return self.update_configuration_module(module=device_settings)

    def get_ospf_database(self):
        """
        Get the OSPF link state database summary
        :return:
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_OSPF_DB",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        return self.get_html_results_from_action_key(action_key=action_key)

    def get_ospf_neighbors(self):
        """
        Get all the OSPF neighbors and associated info
        :return:
        """

        # A token is needed to perform Live Mode API Calls
        # If token is empty then get a token
        if not self.live_mode_token:
            self.set_live_mode_token()

        method = 'liveMode/requestLiveActions'
        params = {
                  "actions": [
                    {
                      "action": "runDiagnostics",
                      "parameters": {
                        "tests": [
                          {
                            "name": "QUAGGA_OSPF_TBL",
                            "parameters": [
                                "\"{}\""
                            ]
                          }
                        ]
                      }
                    }
                  ],
                  "token": self.live_mode_token
                }

        # Execute API call
        action_result = self.client.call_api(method=method, params=params)

        # Obtain live action's key
        action_key = action_result['actionsRequested'][0]['actionId']

        # Look up the live action's results based on the action key
        ospf_neighbors_html = self.get_html_results_from_action_key(action_key=action_key)
        return self.parse_ospf_neighbors_html(html_response=ospf_neighbors_html)

    @staticmethod
    def parse_ospf_neighbors_html(html_response):
        """
        Parses OSPF Neighbors HTML response

        Velocloud responds with HTML text when requesting Remote Diagnostics command: Show OSPF Neighbors

        The following is an example of the HTML response:
        Neighbor ID Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
        192.168.184.2     0 Full/DROther      32.616s 192.168.184.2   GE2:192.168.184.1        0     0     0

        This function will parse each neighbor with its properties and return it in a list
        :param html_response: OSPF Neighbors HTML response
        :return: OSPF Neighbors parsed in a list of dict
        """
        html_response_lines = html_response.splitlines()

        # Find header start
        # Header looks like:
        # Neighbor ID Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
        header_start = 0
        for item in range(0, len(html_response_lines)):
            if 'Neighbor ID' in html_response_lines[item] and 'Pri' in html_response_lines[item] and 'Dead' in \
                    html_response_lines[item]:
                header_start = item

        ospf_neighbors = []
        # Get all entries after the table header
        for entry in html_response_lines[header_start + 1:]:
            """
            Split each entry so obtain each column
            entry example:
            192.168.184.2     0 Full/DROther      32.616s 192.168.184.2   GE2:192.168.184.1        0     0     0
            after its splits:
            ["192.168.184.2", "0", "Full/DROther", "32.616s", "192.168.184.2", "GE2:192.168.184.1", "0", "0", "0"]
            """
            entry_split = entry.split()
            if len(entry_split) == 9:
                neighbor = {
                    'Neighbor ID': entry_split[0],
                    'Pri': entry_split[1],
                    'State': entry_split[2],
                    'Dead Time': entry_split[3],
                    'Address': entry_split[4],
                    'Interface': entry_split[5],
                    'RXmtL': entry_split[6],
                    'RqstL': entry_split[7],
                    'DBsmL': entry_split[8]
                }
                ospf_neighbors.append(neighbor)

        return ospf_neighbors

    def disable_ospf_md5_authentication(self, ospf_interface_name):
        """
        Disable OSPF MD5 Authentication on an OSPF Interface
        :param ospf_interface_name: Interface name to disable OSPF MD5 Authentication on
        :return: API response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Find the OSPF Interface
        ospf_interface = None
        for routed_interface in device_settings['data']['routedInterfaces']:
            if routed_interface['name'] == ospf_interface_name:
                ospf_interface = routed_interface

        if ospf_interface is None:
            raise ValueError(f'Interface: \'{ospf_interface_name}\' was not found in Edges Routed Interfaces.')

        # Disable MD5 on OSPF Interface
        ospf_interface['ospf']['authentication'] = False
        ospf_interface['ospf']['authId'] = None
        ospf_interface['ospf']['authPassphrase'] = None

        return self.update_configuration_module(module=device_settings)

    def enable_ospf_md5_authentication(self, ospf_interface_name, key_id, password):
        """
        Enable OSPF MD5 Authentication on an OSPF Interface
        :param ospf_interface_name: Interface name to enable OSPF MD5 Authentication on
        :param key_id: MD5 key id, number from 1 - 255, default 1
        :param password: MD5 password
        :return: API response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Find the OSPF Interface
        ospf_interface = None
        for routed_interface in device_settings['data']['routedInterfaces']:
            if routed_interface['name'] == ospf_interface_name:
                ospf_interface = routed_interface

        if ospf_interface is None:
            raise ValueError(f'Interface: \'{ospf_interface_name}\' was not found in Edges Routed Interfaces.')

        # Enable MD5 on OSPF Interface
        ospf_interface['ospf']['authentication'] = True
        ospf_interface['ospf']['authId'] = key_id
        ospf_interface['ospf']['authPassphrase'] = password

        return self.update_configuration_module(module=device_settings)


# Class for LAN Sde NAT Testing
class LANSideNatVelocloudEdge(VeloCloudEdge):

    def __init__(self, edge_id, enterprise_id, cpe_ssh_port=None):
        super().__init__(edge_id, enterprise_id, cpe_ssh_port=cpe_ssh_port)

    def get_voice_segment_vlan(self, voice_segment_name=Globals.VOICE_SEGMENT_NAME):
        """
        Get Voice VLAN Configurable information
        :return: Voice VLAN information
        """

        configurable_vlans = self.get_all_configure_vlans()

        for vlan in configurable_vlans:
            if vlan['name'] == voice_segment_name:
                return vlan

    def add_nat_rules_to_segment(self, segment_name, rules:list, dual_rules:list):
        """
        Add NAT rules to a Segment
        :param segment_name: Name of segment you want to add rules to
        :param rules: NAT Source or Destination rules, must be as a list
        :param dual_rules: NAT Source and Destination rules, must be as a list
        :return:
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        # Look for the segment we want to modify
        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Add NAT Rules
                print(f"Adding the following LAN-Side NAT rules to {segment_name} segment... \n"
                      f"NAT Source or Destination: {rules}\n"
                      f"NAT Source and Destination: {dual_rules}\n")
                segment['nat'] = {
                    'rules': rules,
                    'dualRules': dual_rules,
                    'override': True
                }

                return self.update_configuration_module(module=device_settings)

    def delete_all_nat_rules_from_segment(self, segment_name):
        """
        Delete All NAT rules from Segment
        :param segment_name: Name of segment you want to delete rules from
        :return: API Response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                segment.pop('nat', None)

        return self.update_configuration_module(module=device_settings)

    def add_static_route_rule_to_segment(self, rule, segment_name='Voice'):
        """
        Add Static Routes to a Segment
        :param segment_name: Name of segment you want to add rules to
        :param rule: Static Route rule

        example of rule:
          {
            "destination": "172.16.223.0",
            "netmask": "255.255.255.0",
            "sourceIp": null,
            "gateway": "192.168.223.1",
            "cost": 0,
            "preferred": true,
            "description": "",
            "cidrPrefix": "24",
            "wanInterface": "",
            "subinterfaceId": -1,
            "icmpProbeLogicalId": null,
            "vlanId": null,
            "advertise": true
          }
        :return: API Response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Add route to segment
                segment['routes']['static'].append(rule)

        return self.update_configuration_module(module=device_settings)

    def delete_all_static_routes_from_segment(self, segment_name='Voice'):
        """
        Delete all Static Routes from a Segment
        :param segment_name: Name of segment to delete routes from
        :return: API Response
        """

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for segment in device_settings['data']['segments']:
            if segment['segment']['name'] == segment_name:
                # Add route to segment
                segment['routes']['static'] = []

        return self.update_configuration_module(module=device_settings)

    def set_advertise_on_vlan(self, advertise_enabled:bool, vlan_name='Voice'):

        device_settings = self.get_module_from_edge_specific_profile(module_name='deviceSettings')

        for network in device_settings['data']['lan']['networks']:
            if network['name'] == vlan_name:
                network['advertise'] = advertise_enabled

        return self.update_configuration_module(module=device_settings)



# if __name__ == "main":
#     VeloCloudEdge.add_business_policy_rule_to_segment()
