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
# 1.) Create Edge
# 2.) Get active WAN interfaces
# 3.) Start IxLoad
# 4.) Set Business Policy to prefer WAN1
# 5.) Flush Flows
# 6.) List active flows and verify for WAN1
# 7.) Remove Business policy preferring WAN1
# 8.) Set Business Policy to prefer WAN2
# 9.) Flush Flows
# 10.) List active flows and verify for WAN2
# 11.) Remove Business Policy preferring WAN2
# 12.) Clean Up


from my_velocloud.VelocloudEdge import VeloCloudEdge
from ix_load.Modules.IxL_RestApi import *
from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi

DUT_EDGE: VeloCloudEdge


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    return DUT_EDGE


def main():
    # Get active WAN Interfaces
    active_wan_interfaces = []
    active_wan_interfaces = edge.get_active_wan_interfaces()

    # For each interface - add the Business Policy, flush the flows, run traffic, and remove the Business Policy
    for interface in active_wan_interfaces:
        interface_name = interface['interface']
        interface_ip = interface['ip address']

        # Add Business Policy rule to prefer interface
        edge.add_business_policy_rule_to_prefer_interface(
            segment_name='Voice Segment', affected_interface=interface_name
        )

        print(f'Business Policy added for interface {interface_name}. Sleeping for 5 seconds.')
        time.sleep(5)
        print()

        # Flush flows
        print('Flushing flows.')
        edge.remote_diagnostics_flush_flows()

        print('\nConnecting to IxLoad')
        # Enable IxLoad for FTP throughput testing
        ix_load = IxLoadApi()
        ix_load.connect(ixLoadVersion=ix_load.ixLoadVersion)
        print('\nLoading IxLoad config file')
        ix_load.loadConfigFile(rxfFile="C:\\Users\\dataeng\\Documents\\Ixia\\IxLoad\\Repository\\Dev_VeloSingle3400+FTP2Ixia.rxf")
        print('\nForcing ownership')
        ix_load.enableForceOwnership()
        print('\nEnabling IxLoad analyzer')
        ix_load.enableAnalyzerOnAssignedPorts()
        print('\nStarting IxLoad')
        ix_load.runTraffic()

        statsDict = {
            'FTPClient': [{'caption': 'Throughput (Kbps)', 'operator': '>', 'expect': 0}]
        }

        ix_load.pollStatsAndCheckStatResults(statsDict=statsDict)

        # TODO: List flows to verify traffic is being sent over correct interface
        print('\nTraffic completed for 5 minutes. Sleeping for 30 seconds')
        time.sleep(30)

        # Remove Business Policy rule that prefers interface
        edge.remove_business_policy_rule_from_preferred_interface(
            segment_name='Voice Segment', affected_interface=interface_name
        )

        print(f'\nBusiness Policy removed from interface {interface_name}.')


if __name__ == '__main__':
    edge = create_edge(edge_id=240, enterprise_id=1)
    main()
