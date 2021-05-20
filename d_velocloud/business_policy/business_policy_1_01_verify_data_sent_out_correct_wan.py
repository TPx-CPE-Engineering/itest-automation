# Created by: cody.hill@tpx.com
# Creation Date: 5/19/2021
#
# Test Case: 
# Business Policy - 1.01
# Verify data traffic is sent out correct WAN interface when configured in Business Policy
#
# Usage: 
# Can be tested using ICMP ping. Otherwise, use Ixia to send FTP traffic, then steer it to a specific connection in Business Policy. 
# (Configure > Edges > Business Policy > New Rule)
#
# Steps: 
# 1.)  Get VeloCloud Edge
# 2.)  Get active Edge WAN interfaces
# 3.)  Get Edge interface IP addresses
# 4.)  Configure Business Policy to prefer one interface over the other
# 5.)  Flush all active flows
# 6.)  Begin FTP transfer in ixLoad
# 7.)  List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 8.)  Re-configure Business Policy to prefer the other WAN interface
# 9.)  Flush all active flows
# 10.) List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 11.) Stop FTP file transfer
# 12.) Clean up

from my_velocloud.VelocloudEdge import VeloCloudEdge
from my_velocloud.VcoRequestManager import VcoRequestManager

import json, requests

# from ix_load.Modules.IxL_RestApi import *
# from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi

DUT_EDGE: VeloCloudEdge
# IxLoad = IxLoadApi()

def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    return DUT_EDGE

def main():
    # Get WAN Module from Edge Specific Profile
    wan_data = edge.get_module_from_edge_specific_profile(module_name='WAN')

    active_wan_interfaces = []

    # Iterate over each network to get interface associations
    for network in wan_data['data']['networks']:
        interface = network['interface']
        ip_address = network['ipAddress']
        wan_interface = {'interface': interface, 'ip address': ip_address}
        active_wan_interfaces.append(wan_interface)

    wan_1_interface = active_wan_interfaces[0]['interface']
    wan_2_interface = active_wan_interfaces[1]['interface']

    # Set Business Policy to prefer WAN_1
    # qos_data = edge.get_module_from_edge_specific_profile(module_name='QOS')

    method = 'configuration/insertConfigurationModule'

    params = {
        "segments": [
            {
                "segment": {
                    "segmentId": 0,
                    "name": "Global Segment",
                    "type": "REGULAR",
                    "segmentLogicalId": "5dcc72f7-ed23-4bb1-9b7a-c5269d651a05"
                },
                "rules": [
                    {
                        "name": "[AUTOMATION] Prefer GE3",
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
                            "allowConditionalBh": "false",
                            "userDisableConditionalBh": "false",
                            "edge2EdgeRouteAction": {
                                "interface": "GE3",
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "gateway",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": "GE3",
                                "linkCosLogicalId": "",
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": ""
                            },
                            "edge2DataCenterRouteAction": {
                                "interface": "GE3",
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "auto",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": "GE3",
                                "linkCosLogicalId": "",
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": ""
                            },
                            "edge2CloudRouteAction": {
                                "interface": "GE3",
                                "subinterfaceId": -1,
                                "linkInternalLogicalId": "auto",
                                "linkPolicy": "fixed",
                                "routeCfg": {},
                                "routePolicy": "gateway",
                                "serviceGroup": "ALL",
                                "vlanId": -1,
                                "wanlink": "GE3",
                                "linkCosLogicalId": "",
                                "linkOuterDscpTag": "CS0",
                                "linkInnerDscpTag": ""
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
                        },
                        "ruleLogicalId": "37fd8daf-7d54-4812-943d-69f933180f09"
                    }
                ],
                "webProxy": {
                    "providers": []
                }
            }
        ]
    }

    VcoRequestManager.call_api(method=method, params=params)
# #
# def push_business_policy_rule_to_segment(segment='Global Segment'):
#     qos_data = edge.get_module_from_edge_specific_profile(module_name='QOS')
#     print(json.dumps(qos_data, indent=2))
#     # Look for the desired segment
#     # Add rule to segment
#     # Push rule (execute api call)
#     edge.update_configuration_module(module=qos_data)

if __name__ == '__main__':
    edge = create_edge(edge_id=240, enterprise_id=1)
    main()