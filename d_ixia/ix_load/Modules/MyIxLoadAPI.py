import json

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

    def poll_stats_for_1_00_test(self):
        stats_dict = {
            'RTP(VoIPSip)': [{'caption': 'RTP Packets Sent', 'operator': '>', 'expect': 15},
                             {'caption': 'MOS Worst', 'operator': '>', 'expect': 10},
                             {'caption': 'RTP Lost Packets', 'operator': '>', 'expect': 10},
                             {'caption': 'Throughput Outbound (Kbps)', 'operator': '>', 'expect':10},
                             {'caption': 'Throughput Inbound (Kbps)', 'operator': '>', 'expect':10},
                             ]
        }
        self.pollStatsAndCheckStatResults(statsDict=stats_dict)

    def poll_stats_for_1_00_test2(self):
        stats_dict = {
            'RTP(VoIPSip)': ['RTP Packets Sent',
                             'MOS Worst',
                             'RTP Lost Packets',
                             'Throughput Outbound (Kbps)',
                             'Throughput Inbound (Kbps)',
                             ]
        }
        stats = self.pollStats(statsDict=stats_dict, exitAfterPollingIteration=10)
        print(json.dumps(stats, indent=2))
