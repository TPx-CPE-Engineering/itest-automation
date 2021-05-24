# Created by: cody.hill@tpx.com
# Creation Date: 5/19/2021
#
# Test Case: 
# Business Policy - 1.01
# Verify data traffic is sent out correct WAN interface when configured in Business Policy
#
# Usage: 
# Can be tested using ICMP ping. Otherwise, use Ixia to send FTP traffic, then steer it to
# a specific connection in Business Policy.
# (Configure > Edges > Business Policy > New Rule)
#
# Steps:
# 1.)  Get VeloCloud Edge
# 2.)  Get active Edge WAN interfaces
# 3.)  Configure Business Policy to prefer one interface over the other
# 4.)  Flush all active flows
# 5.)  Begin FTP transfer in ixLoad
# 6.)  List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 7.)  Re-configure Business Policy to prefer the other WAN interface
# 8.)  Flush all active flows
# 9.)  List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 10.) Stop FTP file transfer
# 11.) Clean up

from my_velocloud.VelocloudEdge import VeloCloudEdge
import json, time

# from ix_load.Modules.IxL_RestApi import *
# from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi

DUT_EDGE: VeloCloudEdge
# IxLoad = IxLoadApi()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    return DUT_EDGE


def main():
    # Get active WAN Interfaces
    active_wan_interfaces = edge.get_active_wan_interfaces()

    wan_1_interface = active_wan_interfaces[0]['interface']
    wan_2_interface = active_wan_interfaces[1]['interface']

    # Add Business Policy rule to prefer WAN 1
    edge.add_business_policy_rule_to_segment(segment_name='Global Segment')
    print('Business policy added. Sleeping for 10 seconds.')
    time.sleep(10)
    print()

    # Flush flows
    print('Flushing flows.')
    edge.remote_diagnostics_flush_flows()

    # Remove Business Policy rule that prefers WAN 1
    edge.remove_business_policy_rule_from_segment(segment_name='Global Segment')
    print()
    print('Business Policy removed.')


if __name__ == '__main__':
    edge = create_edge(edge_id=240, enterprise_id=1)
    main()

    # Leaving for later
    # rule = {
    #     "name": "[AUTOMATION] Prefer GE3",
    #     "match": {
    #         "appid": -1,
    #         "classid": -1,
    #         "dscp": -1,
    #         "sip": "any",
    #         "sport_high": -1,
    #         "sport_low": -1,
    #         "ssm": "255.255.255.255",
    #         "svlan": -1,
    #         "os_version": -1,
    #         "hostname": "",
    #         "dip": "any",
    #         "dport_low": -1,
    #         "dport_high": -1,
    #         "dsm": "255.255.255.255",
    #         "dvlan": -1,
    #         "proto": -1,
    #         "s_rule_type": "prefix",
    #         "d_rule_type": "prefix"
    #     },
    #     "action": {
    #         "routeType": "edge2Any",
    #         "allowConditionalBh": False,
    #         "userDisableConditionalBh": False,
    #         "edge2EdgeRouteAction": {
    #             "interface": "GE3",
    #             "subinterfaceId": -1,
    #             "linkInternalLogicalId": "auto",
    #             "linkPolicy": "fixed",
    #             "routeCfg": {},
    #             "routePolicy": "gateway",
    #             "serviceGroup": "ALL",
    #             "vlanId": -1,
    #             "wanlink": "GE3",
    #             "linkCosLogicalId": None,
    #             "linkOuterDscpTag": "CS0",
    #             "linkInnerDscpTag": None
    #         },
    #         "edge2DataCenterRouteAction": {
    #             "interface": "GE3",
    #             "subinterfaceId": -1,
    #             "linkInternalLogicalId": "auto",
    #             "linkPolicy": "fixed",
    #             "routeCfg": {},
    #             "routePolicy": "auto",
    #             "serviceGroup": "ALL",
    #             "vlanId": -1,
    #             "wanlink": "GE3",
    #             "linkCosLogicalId": None,
    #             "linkOuterDscpTag": "CS0",
    #             "linkInnerDscpTag": None
    #         },
    #         "edge2CloudRouteAction": {
    #             "interface": "GE3",
    #             "subinterfaceId": -1,
    #             "linkInternalLogicalId": "auto",
    #             "linkPolicy": "fixed",
    #             "routeCfg": {},
    #             "routePolicy": "gateway",
    #             "serviceGroup": "ALL",
    #             "vlanId": -1,
    #             "wanlink": "GE3",
    #             "linkCosLogicalId": None,
    #             "linkOuterDscpTag": "CS0",
    #             "linkInnerDscpTag": None
    #         },
    #         "QoS": {
    #             "type": "transactional",
    #             "rxScheduler": {
    #                 "bandwidth": -1,
    #                 "bandwidthCapPct": -1,
    #                 "queueLen": -1,
    #                 "burst": -1,
    #                 "latency": -1,
    #                 "priority": "normal"
    #             },
    #             "txScheduler": {
    #                 "bandwidth": -1,
    #                 "bandwidthCapPct": -1,
    #                 "queueLen": -1,
    #                 "burst": -1,
    #                 "latency": -1,
    #                 "priority": "normal"
    #             }
    #         },
    #         "sla": {
    #             "latencyMs": "0",
    #             "lossPct": "0.0",
    #             "jitterMs": "0"
    #         },
    #         "nat": {
    #             "sourceIp": "no",
    #             "destIp": "no"
    #         }
    #     }
    # }