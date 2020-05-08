from ixnetwork_restpy import SessionAssistant, Files, StatViewAssistant
import time


def main():
    session_assistant = SessionAssistant(IpAddress='127.0.0.1',
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=True)

    ix_network = session_assistant.Ixnetwork
    test_platform = session_assistant.TestPlatform

    ix_network.LoadConfig(Files('C:\\Users\\dataeng\\Desktop\\Juan_ix_test.ixncfg'))

    vports = ix_network.Vport.find()

    v_ports_state_up = False
    while not v_ports_state_up:
        vports = ix_network.Vport.find()

        for vport in vports:
            print('checking for port connection status...')
            print(f'port connection status: {vport.ConnectionState}')
            if not vport.ConnectionState == 'connectedLinkUp':
                v_ports_state_up = False
                break
            v_ports_state_up = True

        time.sleep(5)
        print('sleeping...')

    traffic = ix_network.Traffic
    print(f'Traffic state: {traffic.State}')

    print('Starting all protocols')
    ix_network.StartAllProtocols()
    print('Sleeping for 30 seconds...')
    time.sleep(30)

    print('Starting Stateful Traffic...')
    traffic.StartStatefulTraffic()

    # print('Sleeping for 60 seconds...')
    # time.sleep(60)
    #
    #
    # print('Stopping Traffic...')
    # traffic.StopStatefulTraffic()
    # time.sleep(20)
    #
    # print('Stopping Protocols...')
    # ix_network.StopAllProtocols()
    # time.sleep(20)

def get_stats():
    session_assistant = SessionAssistant(IpAddress='127.0.0.1',
                                         LogLevel=SessionAssistant.LOGLEVEL_INFO,
                                         ClearConfig=False)

    ix_network = session_assistant.Ixnetwork
    test_platform = session_assistant.TestPlatform

    print(StatViewAssistant.GetViewNames(ix_network))

    traffic_statistics = session_assistant.StatViewAssistant('Traffic Item Statistics')
    print(traffic_statistics)


if __name__ == '__main__':
    # main()
    get_stats()