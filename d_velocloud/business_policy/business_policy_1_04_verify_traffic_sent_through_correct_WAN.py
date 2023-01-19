from business_policy_class import BPVeloCloudEdge
import json


DUT_EDGE: BPVeloCloudEdge


def get_public_interfaces():
    interfaces = DUT_EDGE.get_active_wan_interfaces()
    interfaces = json.loads(interfaces)

    all_interfaces = []
    for interface in interfaces:
        all_interfaces.append(interface['name'])

    print(all_interfaces)


def route_icmp_traffic_to_wan_interface(interface_ip):
    interfaces = DUT_EDGE.get_active_wan_interfaces()
    interfaces = json.loads(interfaces)

    desired_interface = None
    for interface in interfaces:
        if interface['name'] == interface_ip:
            desired_interface = interface

    print(json.dumps(desired_interface, indent=2))

    if desired_interface:
        rule = {
            "name": F"Direct ICMP Traffic to WAN {interface_ip}",
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
                    "interface": "GE3",
                    "subinterfaceId": -1,
                    "linkInternalLogicalId": "auto",
                    "linkPolicy": "fixed",
                    "routeCfg": {},
                    "routePolicy": "gateway",
                    "serviceGroup": "ALL",
                    "vlanId": -1,
                    "wanlink": "GE3",
                    "linkCosLogicalId": None,
                    "linkOuterDscpTag": "CS0",
                    "linkInnerDscpTag": None
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
                    "linkCosLogicalId": None,
                    "linkOuterDscpTag": "CS0",
                    "linkInnerDscpTag": None
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


def did_icmp_traffic_increase(interface):
    pass


def create_edge(edge_id, enterprise_id, ssh_port):
    global DUT_EDGE
    DUT_EDGE = BPVeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
    DUT_EDGE.add_business_policy_rule_to_prefer_interface()
    return DUT_EDGE


if __name__ == '__main__':
    main()
