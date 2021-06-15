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
        self.my_stats = []

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

    def poll_inbound_outbound_throughput_stats(self):
        statsDict = {
            'restStatViews/18': ['Throughput Inbound (Kbps)',
                                 'Throughput Outbound (Kbps)',
                                 'RTP One Way Delay (Avg) [us]'
                                 ]
        }

        pollStatInterval = 2
        exitAfterPollingIteration = None
        waitForRunningStatusCounter = 0
        waitForRunningStatusCounterExit = 120
        pollStatCounter = 0

        while True:
            currentState = self.getActiveTestCurrentState(silentMode=True)
            self.logInfo('ActiveTest current status: %s. ' % currentState)
            if currentState == 'Running':
                if statsDict is None:
                    time.sleep(1)
                    continue

                # statType:  HTTPClient or HTTPServer (Just a example using HTTP.)
                # statNameList: transaction success, transaction failures, ...
                for statType, statNameList in statsDict.items():
                    self.logInfo('\n%s:' % statType, timestamp=False)
                    statUrl = self.sessionIdUrl + '/ixLoad/stats/' + statType + '/values'
                    response = self.getStats(statUrl)
                    highestTimestamp = 0
                    # Each timestamp & stat-names: values
                    for eachTimestamp, valueList in response.json().items():
                        if eachTimestamp == 'error':
                            raise IxLoadRestApiException(
                                'pollStats error: Probable cause: Mis-configured stat names to retrieve.')

                        if int(eachTimestamp) > highestTimestamp:
                            highestTimestamp = int(eachTimestamp)

                    if highestTimestamp == 0:
                        time.sleep(3)
                        continue

                    # Get the interested stat names only
                    for statName in statNameList:
                        if statName in response.json()[str(highestTimestamp)]:
                            statValue = response.json()[str(highestTimestamp)][statName]
                            if not statValue == 0:
                                self.my_stats.append({'time': self.getTime().split('.')[0],
                                                      'stat name': statName,
                                                      'stat value': statValue})
                            # self.my_stats.append([self.getTime().split('.')[0], statName, statValue])
                            self.logInfo('\t%s: %s' % (statName, statValue), timestamp=False)
                        else:
                            self.logError('\tStat name not found. Check spelling and case sensitivity: %s' % statName)

                time.sleep(pollStatInterval)

                if exitAfterPollingIteration and pollStatCounter >= exitAfterPollingIteration:
                    self.logInfo(
                        'pollStats exitAfterPollingIteration is set to {} iterations. Current runtime iteration is {}. Exiting PollStats'.format(
                            exitAfterPollingIteration, pollStatCounter))
                    return

                pollStatCounter += 1

            elif currentState == "Unconfigured":
                break

            else:
                # If currentState is "Stopping Run" or Cleaning
                if waitForRunningStatusCounter < waitForRunningStatusCounterExit:
                    waitForRunningStatusCounter += 1
                    self.logInfo('\tWaiting {0}/{1} seconds'.format(waitForRunningStatusCounter,
                                                                    waitForRunningStatusCounterExit), timestamp=False)
                    time.sleep(1)
                    continue

                if waitForRunningStatusCounter == waitForRunningStatusCounterExit:
                    return 1

    def print_inbound_outbound_throughput_delay_consistency(self):
        # test_pass = True
        # for inbound_value, outbound_value in zip(inbound_values, outbound_values):
        #     if abs(inbound_value['stat_value'] - outbound_value['stat_value']) > max_difference:
        #         test_pass = False
        #         break
        #
        # if test_pass:
        #     print({'Throughput Test': 'Passed'})
        #     # print(f'Test Passed.')
        #     print({'Message': f'There was not a time when Throughput Inbound (Kbps) and Throughput Outbound (Kbps) had values '
        #           f'differ more than {max_difference} Kbps.'})
        # else:
        #     print({'Throughput Test': 'Failed'})
        #     # print(f'Test Failed.')
        #     for inbound_value, outbound_value in zip(inbound_values, outbound_values):
        #         if abs(inbound_value['stat_value'] - outbound_value['stat_value']) > max_difference:
        #             print(f"Error: There was a value difference greater than {max_difference} between "
        #                   f"{inbound_value['stat_name']} and {outbound_value['stat_name']} at time "
        #                   f"{inbound_value['stat_time']}.")
        #
        # for data in delay_values:
        #     print(f"{data['stat_time']} - {data['stat_value']}")
        #
        # print('\nTime' + '-'*12 + 'Throughput Inbound (Kbps)' + '-'*12 + 'Throughput Outbound')
        #
        # for in_value, out_value in zip(inbound_values, outbound_values):
        #     if in_value['stat_time'] != out_value['stat_time']:
        #         continue
        #     else:
        #         print(str(in_value['stat_time']) + '-'*12 + str(in_value['stat_value']) + '-'*12 +
        #               str(out_value['stat_value']))
        stats = self.my_stats
        headers = ['Time', 'Throughput Inbound (Kbps)', 'Throughput Outbound (Kbps)', 'RTP One Way Delay (Avg) [us]']
        data = []
        for stat in stats:
            time = stat['time']
            next_stat = False
            for d in data:
                if time in d:
                    next_stat = True
            if next_stat:
                continue

            values = [time]
            for stat2 in stats:
                if stat2['time'] == time:
                    values.append(stat2['stat value'])

            data.append(values)

        col_width = 0
        for d in data:
            for value in d:
                if len(str(value)) > col_width:
                    col_width = len(str(value))

        for header in headers:
            if len(header) > col_width:
                col_width = len(header)
        col_width += 2

        print("".join(header.ljust(col_width) for header in headers))
        for d in data:
            print("".join(str(value).ljust(col_width) for value in d))

    def check_for_inbound_outbound_throughput_delay_consistency(self):
        stats = self.my_stats
        data = []
        for stat in stats:
            time = stat['time']
            next_stat = False
            for d in data:
                if time in d:
                    next_stat = True
            if next_stat:
                continue

            values = [time]
            for stat2 in stats:
                if stat2['time'] == time:
                    values.append(stat2['stat value'])

            data.append(values)

        warnings_count = 0

        if len(data) == 0:
            print({'test result': 'Failed'})
            return

        for data_point in data:
            if not len(data_point) == 4:
                continue

            time_stat = data_point[0]
            inbound_stat = data_point[1]
            outbound_stat = data_point[2]
            delay_stat = data_point[3]

            if inbound_stat > 149 or inbound_stat < 145:
                print({"warning": f"Throughput Inbound (Kbps) was not between passing threshold 149-145 at time "
                                  f"{time_stat}. Stat value: {inbound_stat}"})
                warnings_count += 1
            if outbound_stat > 149 or outbound_stat < 145:
                print({"warning": f"Throughput Outbound (Kbps) was not between passing threshold 149-145 at time "
                                  f"{time_stat}. Stat value: {outbound_stat}"})
                warnings_count += 1
            if delay_stat > 1500:
                print({"warning": f"Delay was not is passing threshold greater than 1500 at time {time_stat}. "
                                  f"Stat value: {delay_stat}"})
                warnings_count += 1

        if warnings_count <= 10:
            print({'test result': 'Passed'})
        else:
            print({'test result': 'Failed'})
