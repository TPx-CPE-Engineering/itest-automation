import time
from my_velocloud.VelocloudEdge import VeloCloudEdge
from ix_load.Modules.IxL_RestApi import *
import json
from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi

DUT_EDGE: VeloCloudEdge

IxLoad = IxLoadApi()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)


def check_if_application_traffic_has_priority_set_to_multi_path_high(segment_name, application_name):
    # Configure > Profiles > CPE Engineering Base Profile
    enterprise_profile = DUT_EDGE.get_enterprise_profile()

    qos_module = None
    for module in enterprise_profile['modules']:
        if module['name'] == 'QOS':
            qos_module = module

    segment = None
    for seg in qos_module['data']['segments']:
        if seg['segment']['name'] == segment_name:
            segment = seg

    has_high_priority = False
    has_multipath_network_service = False
    for rule in segment['rules']:
        if rule['name'] == application_name:
            # Check priority if High
            if rule['action']['QoS']['rxScheduler']['priority'] == 'high' and \
            rule['action']['QoS']['txScheduler']['priority'] == 'high':
                has_high_priority = True

            # Check Network Service if Multi-Path
            if rule['action']['edge2CloudRouteAction']['routePolicy'] == 'gateway':
                has_multipath_network_service = True

    if has_high_priority and has_multipath_network_service:
        return True
    else:
        return False


def check_if_static_route_is_in_enterprise_gateway(segment_name, static_route):

    enterprise_gateway = DUT_EDGE.get_enterprise_gateway_handoff()

    segment = None
    for seg in enterprise_gateway['value']['segments']:
        if seg['segment']['name'] == segment_name:
            segment = seg

    gateways = []
    for gateway in segment['overrides']['staticRoutes']:
        gateways.append(gateway)

    has_static_route = []
    for gateway in gateways:
        found_static_route = False
        for subnet in segment['overrides']['staticRoutes'][gateway]['subnets']:
            if subnet['cidrIp'] == static_route:
                found_static_route = True
                break

        has_static_route.append(found_static_route)

    if False in has_static_route:
        return False
    else:
        return True


def connect_ix_load():
    # api_server_ip = '127.0.0.1'
    # ixload_version = '8.50.115.542'
    config = "C:\\Users\\dataeng\\Documents\\Ixia\\IxLoad\\Repository\\Dev_Velo620HA-g711+VoiceBsoftFXSStressTest_1-50+Acme+FTP2Ixia.rxf"

    stats_dict = {
        'RTP(VoIPSip)': [{'caption': 'RTP Packets Sent', 'operator': '>', 'expect': 15},
                         {'caption': 'RTP Packets Received', 'operator': '>', 'expect': 10},
                         {'caption': 'MOS Per Call Worst', 'operator': '>', 'expect': 10}
                         ]
    }

    # ixload_rest_client = Main(apiServerIp=api_server_ip,
    #                           apiServerIpPort=8443)
    #
    # # To delete all the sessions in Ix Load
    # # r = ixload_rest_client.delete(restApi='https://127.0.0.1:8443/api/v0/sessions')
    #
    # ixload_rest_client.connect(ixLoadVersion=ixload_version)
    # ixload_rest_client.enableDebugLogFile = False
    #
    # print('Loading config file...')
    # ixload_rest_client.loadConfigFile(rxfFile=config)
    # print('Config file loaded.')
    #
    # ixload_rest_client.enableForceOwnership()
    # ixload_rest_client.enableAnalyzerOnAssignedPorts()
    # ixload_rest_client.configTimeline(name='Timeline1', sustainTime=1)
    #
    # ixload_rest_client.runTraffic()
    #
    # ixload_rest_client.pollStatsAndCheckStatResults(statsDict=stats_dict)
    #
    # test_results = ixload_rest_client.getTestResults()
    #
    # ixload_rest_client.waitForActiveTestToUnconfigure()
    # # ixload_rest_client.gracefulStopRun()
    #
    # print('Deleting Session...')
    # ixload_rest_client.deleteSessionId()
    # print('Session deleted.')
    #
    # print(test_results)

    global IxLoad
    IxLoad.start_test(rxf_config_file=config, stats_dict=stats_dict)

    print('\n\n\n')
    print(IxLoad.testResults)


def start_ix_load():
    print('todo')


def get_test_results():
    print('todo')


if __name__ == '__main__':
    create_edge(edge_id=246, enterprise_id=1)