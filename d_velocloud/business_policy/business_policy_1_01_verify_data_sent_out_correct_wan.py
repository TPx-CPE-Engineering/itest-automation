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
import json

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

    # Get the current QoS Module
    qos_module = edge.get_module_from_edge_specific_profile(module_name='QOS')

    # Check to see if the segment exists.
    global_segment = None
    for segment in qos_module['data']['segments']:
        if segment['segment']['name'] == 'Global Segment':
            global_segment = segment

    # If the segment does not exist, add the segment itself, as well as the rule
    if global_segment is None:
        # Construct the segment data
        global_segment = {
                        "segment": {
                            "segmentId": 0,
                            "name": "Global Segment",
                            "type": "REGULAR",
                            "segmentLogicalId": "5dcc72f7-ed23-4bb1-9b7a-c5269d651a05"
                        },
                        "rules": [
                            {
                                "name": "[AUTOMATION] Prefer " + wan_1_interface,
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
                                        "interface": wan_1_interface,
                                        "subinterfaceId": -1,
                                        "linkInternalLogicalId": "auto",
                                        "linkPolicy": "fixed",
                                        "routeCfg": {},
                                        "routePolicy": "gateway",
                                        "serviceGroup": "ALL",
                                        "vlanId": -1,
                                        "wanlink": wan_1_interface,
                                        "linkCosLogicalId": "",
                                        "linkOuterDscpTag": "CS0",
                                        "linkInnerDscpTag": ""
                                    },
                                    "edge2DataCenterRouteAction": {
                                        "interface": wan_1_interface,
                                        "subinterfaceId": -1,
                                        "linkInternalLogicalId": "auto",
                                        "linkPolicy": "fixed",
                                        "routeCfg": {},
                                        "routePolicy": "auto",
                                        "serviceGroup": "ALL",
                                        "vlanId": -1,
                                        "wanlink": wan_1_interface,
                                        "linkCosLogicalId": "",
                                        "linkOuterDscpTag": "CS0",
                                        "linkInnerDscpTag": ""
                                    },
                                    "edge2CloudRouteAction": {
                                        "interface": wan_1_interface,
                                        "subinterfaceId": -1,
                                        "linkInternalLogicalId": "auto",
                                        "linkPolicy": "fixed",
                                        "routeCfg": {},
                                        "routePolicy": "gateway",
                                        "serviceGroup": "ALL",
                                        "vlanId": -1,
                                        "wanlink": wan_1_interface,
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
        qos_module['data']['segments'].append(global_segment)

    # If the segment already exists, add the rule to the existing segment
    else:
        # we append the rule to the already existing data
        rule = {
            "name": "[AUTOMATION] Prefer " + wan_1_interface,
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
                    "interface": wan_1_interface,
                    "subinterfaceId": -1,
                    "linkInternalLogicalId": "auto",
                    "linkPolicy": "fixed",
                    "routeCfg": {},
                    "routePolicy": "gateway",
                    "serviceGroup": "ALL",
                    "vlanId": -1,
                    "wanlink": wan_1_interface,
                    "linkCosLogicalId": None,
                    "linkOuterDscpTag": "CS0",
                    "linkInnerDscpTag": None
                },
                "edge2DataCenterRouteAction": {
                    "interface": wan_1_interface,
                    "subinterfaceId": -1,
                    "linkInternalLogicalId": "auto",
                    "linkPolicy": "fixed",
                    "routeCfg": {},
                    "routePolicy": "auto",
                    "serviceGroup": "ALL",
                    "vlanId": -1,
                    "wanlink": wan_1_interface,
                    "linkCosLogicalId": None,
                    "linkOuterDscpTag": "CS0",
                    "linkInnerDscpTag": None
                },
                "edge2CloudRouteAction": {
                    "interface": wan_1_interface,
                    "subinterfaceId": -1,
                    "linkInternalLogicalId": "auto",
                    "linkPolicy": "fixed",
                    "routeCfg": {},
                    "routePolicy": "gateway",
                    "serviceGroup": "ALL",
                    "vlanId": -1,
                    "wanlink": wan_1_interface,
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
        global_segment['rules'].append(rule)

    qos_module['metadata']['override'] = True

    # Update the VeloCloud Edge config module to prefer WAN 1
    update_business_policy = edge.update_configuration_module(module=qos_module)

    print('Business policy added.')

    # Do other things here....

    # Get qos module again to remove business policy --- shouldnt need to
    # qos_module = edge.get_module_from_edge_specific_profile(module_name='QOS')

    # # Get Global Segment again --- shouldnt need to
    # global_segment = None
    # for segment in qos_module['data']['segments']:
    #     if segment['segment']['name'] == 'Global Segment':
    #         global_segment = segment

    # Get Global Segment rules
    global_segment_rules = global_segment['rules']
    # print(json.dumps(global_segment_rules))

    for segment_rule in global_segment_rules:
        if segment_rule['name'] == "[AUTOMATION] Prefer " + wan_1_interface:
            print('rule exists...attempting deletion')
            segment_rule = None

            # print(json.dumps(segment_rule))

            # How to append to global segment rule???
            # global_segment['rules'].append(segment_rule)
        else:
            print('Rule doesnt exist')

    # Clear out ALL segments
    # qos_module['data']['segments'] = []

    # Update the VeloCloud Edge config module to remove the rule from the segment
    update_business_policy = edge.update_configuration_module(module=qos_module)

    # print('Business policy segments removed.')

if __name__ == '__main__':
    edge = create_edge(edge_id=240, enterprise_id=1)

    # Get active WAN Interfaces

    # edge.add_business_policy_rule_to_segment(segment_name='Global Segment')
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
    # edge.add_business_policy_rule_to_segment(rule=rule)
    #
    # edge.remove_business_policy_rule_from_segment(segment_name='Global Segment', rule_name="[AUTOMATION] Prefer GE3")