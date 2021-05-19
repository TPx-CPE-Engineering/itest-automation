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
# 6.)  Begin ICMP ping to VeloCloud Edge - ICMP pings to not create active flows - 
# 6a.) Begin FTP transfer in ixLoad
# 7.)  List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 8.)  Re-configure Business Policy to prefer the other WAN interface
# 9.)  Flush all active flows
# 10.) List active flows from source IP and confirm that data traffic is flowing through matching Business Policy
# 11.) Stop FTP file transfer
# 12.) Clean up

from my_velocloud.VelocloudEdge import VeloCloudEdge
from ix_load.Modules.IxL_RestApi import *
import json
from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi
import time

DUT_EDGE: VeloCloudEdge
IxLoad = IxLoadApi()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    return DUT_EDGE


# def get_active_wan_interfaces():
#     wan_data = edge.get_module_from_edge_specific_profile(module_name='WAN')
#     # print(json.dumps(wan_data, indent=2))
#
#     active_wan_interfaces = []
#     for network in wan_data['data']['networks']:
#         interface = network['interface']
#         ip_address = network['ipAddress']
#         wan_interface = {'interface': interface, 'ip address': ip_address}
#         active_wan_interfaces.append(wan_interface)
#         # active_wan_interfaces.append({'interface': network['interface'], 'ip address': network['ipAddress']})
#     return active_wan_interfaces
def push_business_policy_rule_to_segment(segment='Global Segment'):
    qos_data = edge.get_module_from_edge_specific_profile(module_name='QOS')
    print(json.dumps(qos_data, indent=2))
    # Look for the desired segment
    # Add rule to segment
    # Push rule (execute api call)
    edge.update_configuration_module(module=qos_data)


if __name__ == '__main__':
    edge = create_edge(edge_id=240, enterprise_id=1)
    # activate_interfaces = edge.get_active_wan_interfaces()
    push_business_policy_rule_to_segment()