from d_velocloud.business_policy.business_policy_class import BPVeloCloudEdge
import pandas as pd
import json


DUT_EDGE: BPVeloCloudEdge


def get_wan_links(print_itest_message=False):
    wan_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='WAN')

    wan_links = []
    for network in wan_module['data']['networks']:
        link = {
            'name': network['name'],
            'ipAddress': network['ipAddress'],
            'internalId': network['internalId'],
        }
        wan_links.append(link)

    # print(wan_links)
    # if print_itest_message:
    #     # wan_link_names = [link['name'] for link in wan_links]
    #     # print(f"Available WAN Links: \"{', '.join(wan_link_names)}\"")
    #     print(json.dumps(wan_links))

    return wan_links


def add_bp_rule_to_route_icmp_traffic_to_wan_link(wan_link_ip):
    wan_links = get_wan_links(print_itest_message=False)

    desired_wan_link = None

    for link in wan_links:
        if link['ipAddress'] == wan_link_ip:
            desired_wan_link = link

    if desired_wan_link:
        bp_rule = {
            'name': f'iTest Route ICMP Traffic to WAN Link: {desired_wan_link["ipAddress"]}',
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
                'linkInternalLogicalId': desired_wan_link['internalId'],
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
                'linkInternalLogicalId': desired_wan_link['internalId'],
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
                'linkInternalLogicalId': desired_wan_link['internalId'],
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
        DUT_EDGE.add_business_policy_rule(rule=bp_rule, segment_name='Voice Segment')
        print(f"Business policy rule to route ICMP traffic to {desired_wan_link['ipAddress']} in the Voice Segment added successfully")
    else:
        print({'error': f'No WAN link {wan_link_ip} found'})


def remove_bp_rule_to_route_icmp_traffic_to_wan_link(wan_link_ip):
    rule_name = f'iTest Route ICMP Traffic to WAN Link: {wan_link_ip}'
    DUT_EDGE.remove_business_policy_rule(rule_name=rule_name, segment_name='Voice Segment')
    print(f"Business policy rule to route ICMP traffic to {wan_link_ip} in the Voice Segment removed successfully")


def did_icmp_traffic_increase(wan_link_ip, max_seconds):
    dataframe = DUT_EDGE.get_live_icmp_transport_metrics(max_seconds=max_seconds)
    wan_link_data = dataframe.query(f"Name=='{wan_link_ip}'")

    print(wan_link_data.to_string())
    print('\n')

    icmp_bytes_rx_mean = dataframe['ICMP Bytes Rx'].mean()
    print(f"ICMP Bytes Rx Mean: {icmp_bytes_rx_mean}")

    icmp_bytes_tx_mean = dataframe['ICMP Bytes Tx'].mean()
    print(f"ICMP Bytes Tx Mean: {icmp_bytes_tx_mean}")
    print('\n')

    if icmp_bytes_rx_mean == 0 and icmp_bytes_tx_mean == 0:
        print(f"Did ICMP Traffic Increase: False")
    else:
        print(f"Did ICMP Traffic Increase: True")


def create_edge(edge_id, enterprise_id, ssh_port):
    global DUT_EDGE
    DUT_EDGE = BPVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
    return DUT_EDGE


if __name__ == '__main__':
    create_edge(edge_id=10, enterprise_id=1, ssh_port=2201)
    get_wan_links(print_itest_message=True)
    # add_bp_rule_to_route_icmp_traffic_to_wan_link(wan_link_ip='66.17.13.156')
    # did_icmp_traffic_increase(wan_link_ip='66.17.13.156', max_seconds=300)
    # remove_bp_rule_to_route_icmp_traffic_to_wan_link(wan_link_ip='66.17.13.156')
