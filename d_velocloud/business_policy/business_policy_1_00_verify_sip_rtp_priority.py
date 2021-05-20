from my_velocloud.VelocloudEdge import VeloCloudEdge
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


# def check_if_application_traffic_has_priority_set_to_multi_path_high(segment_name, application_name):
#     # Configure > Profiles > CPE Engineering Base Profile
#     enterprise_profile = DUT_EDGE.get_enterprise_profile()
#
#     qos_module = None
#     for module in enterprise_profile['modules']:
#         if module['name'] == 'QOS':
#             qos_module = module
#
#     segment = None
#     for seg in qos_module['data']['segments']:
#         if seg['segment']['name'] == segment_name:
#             segment = seg
#
#     has_high_priority = False
#     has_multipath_network_service = False
#     for rule in segment['rules']:
#         if rule['name'] == application_name:
#             # Check priority if High
#             if rule['action']['QoS']['rxScheduler']['priority'] == 'high' and \
#             rule['action']['QoS']['txScheduler']['priority'] == 'high':
#                 has_high_priority = True
#
#             # Check Network Service if Multi-Path
#             if rule['action']['edge2CloudRouteAction']['routePolicy'] == 'gateway':
#                 has_multipath_network_service = True
#
#     if has_high_priority and has_multipath_network_service:
#         return True
#     else:
#         return False
#
#
# def check_if_static_route_is_in_enterprise_gateway(segment_name, static_route):
#
#     enterprise_gateway = DUT_EDGE.get_enterprise_gateway_handoff()
#
#     segment = None
#     for seg in enterprise_gateway['value']['segments']:
#         if seg['segment']['name'] == segment_name:
#             segment = seg
#
#     gateways = []
#     for gateway in segment['overrides']['staticRoutes']:
#         gateways.append(gateway)
#
#     has_static_route = []
#     for gateway in gateways:
#         found_static_route = False
#         for subnet in segment['overrides']['staticRoutes'][gateway]['subnets']:
#             if subnet['cidrIp'] == static_route:
#                 found_static_route = True
#                 break
#
#         has_static_route.append(found_static_route)
#
#     if False in has_static_route:
#         return False
#     else:
#         return True


def check_for_ha_going_active_in_edge_events(start_interval):
    # print(f"Start Interval: {start_interval}")
    events = DUT_EDGE.get_enterprise_events(start_interval=start_interval)

    response = {'HA_GOING_ACTIVE Present': False}
    for event in events['data']:
        if event['event'] == 'HA_GOING_ACTIVE':
            response['HA_GOING_ACTIVE Present'] = True

    print(response)
    print(json.dumps(events['data'], indent=2))


if __name__ == '__main__':
    # edge, epoch = create_edge(edge_id=246, enterprise_id=1)
    # check_for_ha_going_active_in_edge_events(start_interval=1620239780887)

    ix_load = IxLoadApi()
    ix_load.connect(ixLoadVersion=ix_load.ixLoadVersion)
    ix_load.loadConfigFile(rxfFile="C:\\Users\\dataeng\\Documents\\Ixia\\IxLoad\\Repository\\Dev_Velo620HA-g711+VoiceBsoftFXSStressTest_1-50+Acme+FTP2Ixia.rxf")
    ix_load.enableForceOwnership()
    ix_load.enableAnalyzerOnAssignedPorts()
    ix_load.runTraffic()
    ix_load.poll_inbound_outbound_throughput_stats()


