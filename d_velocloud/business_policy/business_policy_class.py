from my_velocloud.VelocloudEdge import VeloCloudEdge
from ipaddress import ip_address
from datetime import datetime
import json
import time
import pytz     # TODO install in CPE python venv
import pandas as pd     # TODO install in CPE python venv
import pandas.core.frame
from typing import Optional


class BPVeloCloudEdge(VeloCloudEdge):
    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)

    # Any related to Business Policy(BP) test case/s you can add it here
    def get_active_wan_interfaces(self):
        wan_settings = self.get_module_from_edge_specific_profile(module_name='WAN')
        for link in wan_settings['data']['links']:
            link['isLinkIpAddressPublic'] = not ip_address(link['publicIpAddress']).is_private
        return json.dumps(wan_settings['data']['links'])

    @staticmethod
    def convert_to_datetime(timestamp: int, timezone='UTC'):
        """
        Converts a given Datto timestamp or a Epoch Unix milliseconds timestamp into a datetime
        :param timestamp: Int, Epoch Unix milliseconds timestamp
        :param timezone: Str, pytz timezone, default UTC
        :return: Obj, datetime
        """
        return datetime.fromtimestamp(timestamp / 1000, tz=pytz.timezone(timezone))

    def get_live_icmp_transport_metrics(self, max_seconds) -> Optional[pandas.core.frame.DataFrame]:

        # enter live mode and set live mode token
        self.set_live_mode_token()

        all_data = []

        seconds_to_collect_data = 0
        # print(f"Start time: {datetime.now(tz=pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S')}")
        while seconds_to_collect_data < max_seconds:
            seconds_to_collect_data += 1
            response = self.client.call_api(method='liveMode/readLiveData', params={'token': self.live_mode_token})

            if response['status']['isActive']:
                if response['data']:
                    link_data = response['data']['linkStats']['data']

                    for link in link_data:
                        ts_datetime = self.convert_to_datetime(timestamp=link['timestamp'], timezone='America/Los_Angeles')

                        if link['data']:
                            for entry in link['data']:
                                icmpBytesRx = entry['icmpBytesRx']
                                icmpBytesTx = entry['icmpBytesTx']
                                name = entry['name']
                                d = {
                                    'Time': ts_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                    'Name': name,
                                    'ICMP Bytes Rx': icmpBytesRx,
                                    'ICMP Bytes Tx': icmpBytesTx
                                }
                                all_data.append(d)
            time.sleep(1)

        self.exit_live_mode()

        if len(all_data) != 0:
            df2 = pd.DataFrame(all_data)
            print(df2.to_string())
            return df2
        else:
            print({'error': 'No metrics to show'})
            return None


if __name__ == '__main__':
    edge = BPVeloCloudEdge(edge_id=10, enterprise_id=1)
    edge.get_live_icmp_transport_metrics(max_seconds=180)
