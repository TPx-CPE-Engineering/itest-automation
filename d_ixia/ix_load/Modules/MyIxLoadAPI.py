import json
import time
from d_ixia.ix_load.Modules.IxL_RestApi import Main, IxLoadRestApiException


class IxLoadApi(Main):
    def __init__(self, api_server_ip='127.0.0.1', api_server_ip_port=8443, ixload_version='8.50.115.542',
                 use_https=False, api_key=None, verify_ssl=False, delete_session=True, os_platform='windows',
                 generate_rest_log_file='ixLoad_testLog.txt', poll_status_interval=1, robot_framework_stdout=False):
        super().__init__(apiServerIp=api_server_ip, apiServerIpPort=api_server_ip_port, useHttps=use_https,
                         apiKey=api_key, verifySsl=verify_ssl, deleteSession=delete_session, osPlatform=os_platform,
                         generateRestLogFile=generate_rest_log_file, pollStatusInterval=poll_status_interval,
                         robotFrameworkStdout=robot_framework_stdout)
        self.ixLoadVersion = ixload_version
        self.enableDebugLogFile = False

    def start_test(self, rxf_config_file, stats_dict, enable_force_ownership=True):

        self.connect(ixLoadVersion=self.ixLoadVersion)

        self.loadConfigFile(rxfFile=rxf_config_file)

        if enable_force_ownership:
            self.enableForceOwnership()

        self.enableAnalyzerOnAssignedPorts()
        self.runTraffic()
        self.pollStatsAndCheckStatResults(statsDict=stats_dict)
        self.waitForActiveTestToUnconfigure()
        self.deleteSessionId()

    def check_for_inbound_outbound_throughput_consistency(self, max_difference=1):
        stats = ['Throughput Inbound (Kbps)', 'Throughput Outbound (Kbps)']
        inbound_values = []
        outbound_values = []

        current_state = 'Running'
        while current_state == 'Running':
            if current_state == 'Running':

                stats_url = self.sessionIdUrl + '/ixLoad/stats/restStatViews/18/values'
                rest_stat_views_stats = self.getStats(stats_url)

                highestTimestamp = 0
                # Each timestamp & statnames: values
                for eachTimestamp, valueList in rest_stat_views_stats.json().items():
                    if eachTimestamp == 'error':
                        raise IxLoadRestApiException(
                            'pollStats error: Probable cause: Mis-configured stat names to retrieve.')

                    if int(eachTimestamp) > highestTimestamp:
                        highestTimestamp = int(eachTimestamp)

                if highestTimestamp == 0:
                    time.sleep(3)
                    continue

                for stat in stats:
                    if stat in rest_stat_views_stats.json()[str(highestTimestamp)]:
                        statValue = rest_stat_views_stats.json()[str(highestTimestamp)][stat]
                        if stat == "Throughput Outbound (Kbps)":
                            # outbound_values.append(statValue)
                            outbound_values.append({'stat_time': highestTimestamp, 'stat_name': stat, 'stat_value': statValue})
                        if stat == "Throughput Inbound (Kbps)":
                            # inbound_values.append(statValue)
                            inbound_values.append({'stat_time': highestTimestamp, 'stat_name': stat, 'stat_value': statValue})
            time.sleep(2)
            current_state = self.getActiveTestCurrentState(silentMode=True)

        test_pass = True
        for inbound_value, outbound_value in zip(inbound_values, outbound_values):
            if abs(inbound_value['stat_value'] - outbound_value['stat_value']) > max_difference:
                test_pass = False
                break

        if test_pass:
            print(f'Test Passed.')
            print(f'There was not a time when Throughput Inbound (Kbps) and Throughput Outbound (Kbps) had values '
                  f'differ more than {max_difference} Kbps.')
        else:
            print(f'Test Failed.')
            for inbound_value, outbound_value in zip(inbound_values, outbound_values):
                if abs(inbound_value['stat_value'] - outbound_value['stat_value']) > max_difference:
                    print(f"Error: There was a value difference greater than {max_difference} between "
                          f"{inbound_value['stat_name']} and {outbound_value['stat_name']} at time {inbound_value['stat_time']}.")

        print('\nTime\t\tThroughput Inbound (Kbps)\t\tThroughput Outbound')
        for in_value, out_value in zip(inbound_values, outbound_values):
            if in_value['stat_time'] != out_value['stat_time']:
                continue
            else:
                print(in_value['stat_time'] + '\t\t' + in_value['stat_value'] + '\t\t' + out_value['stat_value'])
