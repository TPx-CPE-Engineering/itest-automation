from my_velocloud.VelocloudEdge import VeloCloudEdge
from ipaddress import ip_address
from datetime import datetime
import json
import time
import pytz     # TODO install in CPE python venv
import pandas as pd     # TODO install in CPE python venv
import pandas.core.frame
from typing import Optional


class BPVeloCloudEdge(VeloCloudEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id, enterprise_id, cpe_ssh_port=ssh_port)

    # Any related to Business Policy(BP) test case/s you can add it here
    def get_active_wan_interfaces(self):
        wan_settings = self.get_module_from_edge_specific_profile(module_name='WAN')
        for link in wan_settings['data']['links']:
            link['isLinkIpAddressPublic'] = not ip_address(link['publicIpAddress']).is_private
        return json.dumps(wan_settings['data']['links'])

    @staticmethod
    def convert_to_datetime(timestamp: int, timezone='UTC'):
        """
        Converts a given Datto timestamp or a Epoch Unix milliseconds timestamp into a datetime
        :param timestamp: Int, Epoch Unix milliseconds timestamp
        :param timezone: Str, pytz timezone, default UTC
        :return: Obj, datetime
        """
        return datetime.fromtimestamp(timestamp / 1000, tz=pytz.timezone(timezone))

    def get_live_icmp_transport_metrics(self, max_seconds) -> Optional[pandas.core.frame.DataFrame]:

        # enter live mode and set live mode token
        self.set_live_mode_token()

        all_data = []

        seconds_to_collect_data = 0
        # print(f"Start time: {datetime.now(tz=pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S')}")
        while seconds_to_collect_data < max_seconds:
            seconds_to_collect_data += 1
            response = self.client.call_api(method='liveMode/readLiveData', params={'token': self.live_mode_token})

            if response['status']['isActive']:
                if response['data']:
                    try:
                        link_data = response['data']['linkStats']['data']
                    except KeyError:
                        continue

                    for link in link_data:
                        ts_datetime = self.convert_to_datetime(timestamp=link['timestamp'], timezone='America/Los_Angeles')

                        if link['data']:
                            for entry in link['data']:
                                icmpBytesRx = entry['icmpBytesRx']
                                icmpBytesTx = entry['icmpBytesTx']
                                name = entry['name']
                                d = {
                                    'Time': ts_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                    'Name': name,
                                    'ICMP Bytes Rx': icmpBytesRx,
                                    'ICMP Bytes Tx': icmpBytesTx
                                }
                                all_data.append(d)
            time.sleep(1)

        self.exit_live_mode()

        if len(all_data) != 0:
            df2 = pd.DataFrame(all_data)
            return df2
        else:
            print({'error': 'No metrics to show'})
            return None

    def add_business_policy_rule(self, rule, segment_name):
        qos_module = self.get_module_from_edge_specific_profile(module_name='QOS')

        qos_desired_segment = None
        if len(qos_module['data']['segments']) != 0:
            # check if the desired segment is already added in the QOS
            for segment in qos_module['data']['segments']:
                if segment['segment']['name'] == segment_name:
                    qos_desired_segment = segment

        if qos_desired_segment is None:
            # Create the desired segment
            segments = self.get_device_settings_segments()

            desired_segment = None
            for segment in segments:
                if segment['segment']['name'] == segment_name:
                    desired_segment = segment

            if desired_segment is None:
                print({'error': f'No segment: {segment_name} found'})
                return

            segment = {
                'segmentId': desired_segment['segment']['segmentId'],
                'name': desired_segment['segment']['name'],
                'type': desired_segment['segment']['type'],
                'segmentLogicalId': 'cc562233-20aa-4716-a613-5556935b4946'
            }

            qos_desired_segment = {
                'segment': segment,
                'rules': [],
                'webProxy': {'providers': []}
            }

        qos_desired_segment['rules'].append(rule)

        qos_module['data']['segments'].append(qos_desired_segment)

        return self.update_configuration_module(module=qos_module)

    def remove_business_policy_rule(self, rule_name, segment_name):
        qos_module = self.get_module_from_edge_specific_profile(module_name='QOS')

        desired_qos_segment = None
        for segment in qos_module['data']['segments']:
            if segment['segment']['name'] == segment_name:
                desired_qos_segment = segment

        if desired_qos_segment is None:
            print({'error': f'No segment: {segment_name} found'})
            return

        new_rules = []
        for rule in desired_qos_segment['rules']:
            if rule['name'] != rule_name:
                new_rules.append(rule)

        desired_qos_segment['rules'] = new_rules

        all_segments = []
        for segment in qos_module['data']['segments']:
            if segment['segment']['name'] != segment_name:
                all_segments.append(segment)
        all_segments.append(desired_qos_segment)

        qos_module['data']['segments'] = all_segments

        return self.update_configuration_module(module=qos_module)


if __name__ == '__main__':
    edge = BPVeloCloudEdge(edge_id=10, enterprise_id=1, ssh_port=2201)
    # edge.get_live_icmp_transport_metrics(max_seconds=180)
    bp_rule = {
            'name': 'Route ICMP Traffic to WAN: 123',
            'match': {
              'appid': 70,
              'classid': -1,
              'dscp': -1,
              'sip': 'any',
              'sport_high': -1,
              'sport_low': -1,
              'ssm': '255.255.255.255',
              'svlan': -1,
              'os_version': -1,
              'hostname': '',
              'dip': 'any',
              'ipVersion': 'IPv4',
              'dport_low': -1,
              'dport_high': -1,
              'dsm': '255.255.255.255',
              'dvlan': -1,
              'dInterface': '',
              'proto': -1,
              's_rule_type': 'prefix',
              'd_rule_type': 'prefix',
              'sInterface': ''
            },
            'action': {
              'routeType': 'edge2Any',
              'userDisableConditionalBh': False,
              'edge2EdgeRouteAction': {
                'interface': 'auto',
                'subinterfaceId': -1,
                'linkInternalLogicalId': '00000001-431e-41c2-95dd-34aa8cda9cb1',
                'linkPolicy': 'fixed',
                'routeCfg': {},
                'routePolicy': 'direct',
                'serviceGroup': 'ALL',
                'vlanId': -1,
                'wanlink': 'auto',
                'linkCosLogicalId': None,
                'linkOuterDscpTag': None,
                'linkInnerDscpTag': None
              },
              'edge2DataCenterRouteAction': {
                'interface': 'auto',
                'subinterfaceId': -1,
                'linkInternalLogicalId': '00000001-431e-41c2-95dd-34aa8cda9cb1',
                'linkPolicy': 'fixed',
                'routeCfg': {},
                'routePolicy': 'auto',
                'serviceGroup': 'ALL',
                'vlanId': -1,
                'wanlink': 'auto',
                'linkCosLogicalId': None,
                'linkOuterDscpTag': None,
                'linkInnerDscpTag': None
              },
              'edge2CloudRouteAction': {
                'interface': 'auto',
                'subinterfaceId': -1,
                'linkInternalLogicalId': '00000001-431e-41c2-95dd-34aa8cda9cb1',
                'linkPolicy': 'fixed',
                'routeCfg': {},
                'routePolicy': 'direct',
                'serviceGroup': 'ALL',
                'vlanId': -1,
                'wanlink': 'auto',
                'linkCosLogicalId': None,
                'linkOuterDscpTag': None,
                'linkInnerDscpTag': None
              },
              'QoS': {
                'type': 'transactional',
                'rxScheduler': {
                  'bandwidth': -1,
                  'bandwidthCapPct': -1,
                  'queueLen': -1,
                  'burst': -1,
                  'latency': -1,
                  'priority': 'normal'
                },
                'txScheduler': {
                  'bandwidth': -1,
                  'bandwidthCapPct': -1,
                  'queueLen': -1,
                  'burst': -1,
                  'latency': -1,
                  'priority': 'normal'
                }
              },
              'nat': {
                'sourceIp': 'no',
                'destIp': 'no'
              },
              'natIpVersion': None,
              'natV6': {
                'sourceIp': 'no',
                'destIp': 'no'
              },
              'sla': {
                'latencyMs': '0',
                'lossPct': '0.0',
                'jitterMs': '0'
              }
            },
            'ruleLogicalId': '209ba481-6e32-41e8-9360-1dd90f206d58'
          }
    # edge.add_business_policy_rule(rule=bp_rule, segment_name='Voice Segment')
    edge.remove_business_policy_rule(rule_name='Route ICMP Traffic to WAN: 123', segment_name='Voice Segment')

