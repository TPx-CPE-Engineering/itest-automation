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
EPOCH = int()

def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, EPOCH
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    EPOCH = int(round(time.time() * 1000))
    return DUT_EDGE, EPOCH

if __name__ == '__main__':
    edge, epoch = create_edge(edge_id=246, enterprise_id=1)
    print(edge)