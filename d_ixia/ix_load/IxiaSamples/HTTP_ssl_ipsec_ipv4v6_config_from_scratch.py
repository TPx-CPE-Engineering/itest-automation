import Utils.IxLoadUtils as IxLoadUtils
import Utils.IxRestUtils as IxRestUtils
import Utils.IxLoadTestSettings as TestSettings
import inspect


#### TEST CONFIG
testSettings = TestSettings.IxLoadTestSettings()
# testSettings.gatewayServer = "machine_ip_address"     # TODO - to be changed by user if he wants to run remote
testSettings.ixLoadVersion = ""                         # TODO - to be changed by user, by default will run on the latest installed version
testSettings.chassisList = ['chassisIpOrHostName']      # TODO - to be changed by user

kArgumentFilePath = r"C:\\Path\\to\\argument\\file"     # TODO - to be changed by user
kArgumentFilePath = kArgumentFilePath.replace("\\\\", "/")

location=inspect.getfile(inspect.currentframe())

testSettings.portListPerCommunity = {
                                        "Traffic1@Network1" : [(1,7,1)],
                                        "Traffic2@Network2" : [(1,7,5)]
                                    }

kStatsToDisplayDict =   {
                            # format: { statSource : [stat name list] }
                            "HTTPClient": ["HTTP Simulated Users", "HTTP Concurrent Connections", "HTTP Requests Successful"],
                            "HTTPServer": ["HTTP Requests Received", "TCP Retries"]
                        }

kCommunities = [
    # format: {option1: value1, option2: value2}
    {},  # default community with no options
    {"tcpAccelerationAllowedFlag": True}  # community with tcpAccelerationAllowedFlag set to True
]

kActivities = {
    # format: {communityName: [activityProtocolAndType1, activityProtocolAndType2]}
    'Traffic1@Network1': ['HTTP Client', 'HTTP Client'],
    'Traffic2@Network2': ['HTTP Server']
}

kNewCommands =  {
                    # format: { agent name : [ { field : value } ] }
                    "HTTPClient1" : [
                                        {
                                            "commandType"   : "GET",
                                            "destination"   : "Traffic2_HTTPServer1:80",
                                            "pageObject"    : "/32k.html",
                                        },
                                        {
                                            "commandType"   : "POST",
                                            "destination"   : "Traffic2_HTTPServer1:80",
                                            "pageObject"    : "/8k.html",
                                            "arguments"     : kArgumentFilePath,
                                        },
                                        {
                                            'commandType': 'GET(SSL)',
                                            "destination": "Traffic2_HTTPServer1:443",
                                            "pageObject": "/1b.html"
                                        }
                                    ],
                    "HTTPClient2" : [
                                        {
                                            "commandType"   : "GET",
                                            "destination"   : "Traffic2_HTTPServer1:80",
                                            "pageObject"    : "/32k.html",
                                        }
                                    ]
                }

# Create a connection to the gateway
connection = IxRestUtils.getConnection(
                        testSettings.gatewayServer,
                        testSettings.gatewayPort,
                        httpRedirect=testSettings.httpRedirect,
                        version=testSettings.apiVersion
                        )
sessionUrl = None

try:
    # Create a session
    IxLoadUtils.log("Creating a new session...")
    sessionUrl = IxLoadUtils.createNewSession(connection, testSettings.ixLoadVersion)
    IxLoadUtils.log("Session created.")

    # Create nettraffics (communities)
    IxLoadUtils.log('Creating communities...')
    IxLoadUtils.addCommunities(connection, sessionUrl, kCommunities)
    IxLoadUtils.log('Communities created.')

    # Create activities
    IxLoadUtils.log('Creating activities...')
    IxLoadUtils.addActivities(connection, sessionUrl, kActivities)
    IxLoadUtils.log('Activities created.')

    # Enable SSL on clients and server
    IxLoadUtils.log('Enabling SSL on HTTP Client and HTTP Server...')
    IxLoadUtils.HttpUtils.enableSSLOnClient(connection, sessionUrl, 'Traffic1@Network1', 'HTTPClient1')
    IxLoadUtils.HttpUtils.enableSSLOnClient(connection, sessionUrl, 'Traffic1@Network1', 'HTTPClient2')
    IxLoadUtils.HttpUtils.enableSSLOnServer(connection, sessionUrl, 'Traffic2@Network2', 'HTTPServer1')

    clientIpv6RangeOptions = {
        'prefix': 112,
        'ipAddress': '::A0A:259',
        'incrementBy': '::1',
        'gatewayAddress': '::0',
        'gatewayIncrement': '::0'
    }
    serverIpv6RangeOptions = {
        'prefix': 112,
        'ipAddress': '::A0A:12D',
        'incrementBy': '::1',
        'gatewayAddress': '::0',
        'gatewayIncrement': '::0'
    }

    IxLoadUtils.log('Adding IPv6 ranges on HTTP Client and HTTP Server...')
    IxLoadUtils.HttpUtils.addIpRange(connection, sessionUrl, 'Traffic1@Network1', 'IP-1', {'ipType': 'IPv6'})
    IxLoadUtils.HttpUtils.addIpRange(connection, sessionUrl, 'Traffic2@Network2', 'IP-2', {'ipType': 'IPv6'})

    IxLoadUtils.log('Changing range options for the IPv6 ranges on HTTP Client and HTTP Server...')
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic1@Network1', 'IP-1', 'rangeList', 'IP-R3', clientIpv6RangeOptions)
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic2@Network2', 'IP-2', 'rangeList', 'IP-R4', serverIpv6RangeOptions)

    IxLoadUtils.log('Adding IPSec plugin on HTTP Client and HTTP Server...')
    IxLoadUtils.HttpUtils.addIpsecPlugin(connection, sessionUrl, 'Traffic1@Network1', 'IP-1')
    IxLoadUtils.HttpUtils.addIpsecPlugin(connection, sessionUrl, 'Traffic2@Network2', 'IP-2')

    ipsecR1RangeOptions = {
        'peerPublicIP': '10.10.0.101'
    }
    ipsecR2RangeOptions = {
        'peerPublicIP': '::A0A:12D',
        'peerPublicIPType': 'IPv6',
        'peerPublicIncrement': '::0',
        'emulatedSubnetIpType': 'IPv6',
        'emulatedSubnet': '::2800:0',
        'emulatedSubnetSuffix': 120,
        'esnIncrementBy': '::100',
        'protectedSubnet': '::4600:0',
        'protectedSubnetSuffix': 120,
        'psnIncrementBy': '::100'
    }
    ipsecR3RangeOptions = {
        'peerPublicIP': '10.10.0.1',
        'emulatedSubnet': '70.0.0.0',
        'protectedSubnet': '40.0.0.0'
    }
    ipsecR4RangeOptions = {
        'peerPublicIP': '::A0A:259',
        'peerPublicIPType': 'IPv6',
        'peerPublicIncrement': '::0',
        'emulatedSubnetIpType': 'IPv6',
        'emulatedSubnet': '::4600:0',
        'emulatedSubnetSuffix': 120,
        'esnIncrementBy': '::100',
        'protectedSubnet': '::2800:0',
        'protectedSubnetSuffix': 120,
        'psnIncrementBy': '::100'
    }

    IxLoadUtils.log('Changing range options for the IPSec ranges on HTTP Client and HTTP Server...')
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic1@Network1', 'IPsec-1', 'rangeList', 'IPsec-R1', ipsecR1RangeOptions)
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic1@Network1', 'IPsec-1', 'rangeList', 'IPsec-R2', ipsecR2RangeOptions)
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic2@Network2', 'IPsec-2', 'rangeList', 'IPsec-R3', ipsecR3RangeOptions)
    IxLoadUtils.HttpUtils.changeRangeOptions(connection, sessionUrl, 'Traffic2@Network2', 'IPsec-2', 'rangeList', 'IPsec-R4', ipsecR4RangeOptions)

    ipsec2PortGroupDataOptions = {
        'role': 'Responder'
    }

    IxLoadUtils.log('Changing the IPSec plugin role to responder on the HTTP server...')
    IxLoadUtils.IpsecUtils.changePortGroupDataOptions(connection, sessionUrl, 'Traffic2@Network2', 'IPsec-2', ipsec2PortGroupDataOptions)

    ipsecTunnelSetupOptions = {
        'testType': 'P2P'
    }
    IxLoadUtils.log('Changing the IPSec tunnel setup options on HTTP Client and HTTP Server...')
    IxLoadUtils.IpsecUtils.changeIpsecTunnelSetupOptions(connection, sessionUrl, 'Traffic1@Network1', 'IPsec-1', ipsecTunnelSetupOptions)
    IxLoadUtils.IpsecUtils.changeIpsecTunnelSetupOptions(connection, sessionUrl, 'Traffic2@Network2', 'IPsec-2', ipsecTunnelSetupOptions)

    IxLoadUtils.log("Clearing chassis list...")
    IxLoadUtils.clearChassisList(connection, sessionUrl)
    IxLoadUtils.log("Chassis list cleared.")

    IxLoadUtils.log("Adding chassis %s..." % (testSettings.chassisList))
    IxLoadUtils.addChassisList(connection, sessionUrl, testSettings.chassisList)
    IxLoadUtils.log("Chassis added.")

    IxLoadUtils.log("Assigning new ports...")
    IxLoadUtils.assignPorts(connection, sessionUrl, testSettings.portListPerCommunity)
    IxLoadUtils.log("Ports assigned.")

    IxLoadUtils.log("Clearing command lists for agents %s..." % (list(kNewCommands)))
    IxLoadUtils.clearAgentsCommandList(connection, sessionUrl, list(kNewCommands))
    IxLoadUtils.log("Command lists cleared.")

    IxLoadUtils.log("Adding new commands for agents %s..." % (list(kNewCommands)))
    IxLoadUtils.addCommands(connection, sessionUrl, kNewCommands)
    IxLoadUtils.log("Commands added.")

    IxLoadUtils.log("Saving repository %s..." % (IxLoadUtils.getRxfName(connection,location)))
    IxLoadUtils.saveRxf(connection, sessionUrl, IxLoadUtils.getRxfName(connection,location))
    IxLoadUtils.log("Repository saved.")

    IxLoadUtils.log("Starting the test...")
    IxLoadUtils.runTest(connection, sessionUrl)
    IxLoadUtils.log("Test started.")

    IxLoadUtils.log("Polling values for stats %s..." % (kStatsToDisplayDict))
    IxLoadUtils.pollStats(connection, sessionUrl, kStatsToDisplayDict)

    IxLoadUtils.log("Test finished.")

    IxLoadUtils.log("Checking test status...")
    testRunError = IxLoadUtils.getTestRunError(connection, sessionUrl)
    if testRunError:
        IxLoadUtils.log("The test exited with the following error: %s" % testRunError)
    else:
        IxLoadUtils.log("The test completed successfully.")

    IxLoadUtils.log("Waiting for test to clean up and reach 'Unconfigured' state...")
    IxLoadUtils.waitForTestToReachUnconfiguredState(connection, sessionUrl)
    IxLoadUtils.log("Test is back in 'Unconfigured' state.")

finally:
    if sessionUrl is not None:
        IxLoadUtils.log("Closing IxLoad session...")
        IxLoadUtils.deleteSession(connection, sessionUrl)
        IxLoadUtils.log("IxLoad session closed.")
