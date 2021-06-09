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

    ix_load = IxLoadApi(api_server_ip='10.255.20.196')
    ix_load.connect(ixLoadVersion=ix_load.ixLoadVersion)
    ix_load.loadConfigFile(rxfFile="C:\\Users\\dataeng\\Documents\\Ixia\\IxLoad\\Repository\\Dev_Velo620HA-g711+VoiceBsoftFXSStressTest_1-50+Acme+FTP2Ixia.rxf")
    ix_load.enableForceOwnership()
    ix_load.enableAnalyzerOnAssignedPorts()
    ix_load.runTraffic()
    ix_load.poll_inbound_outbound_throughput_stats()
    # ix_load.check_for_inbound_outbound_throughput_delay_consistency()
    ix_load.print_inbound_outbound_throughput_delay_consistency()