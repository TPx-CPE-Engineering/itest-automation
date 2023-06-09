import Utils.IxLoadUtils as IxLoadUtils
import Utils.IxRestUtils as IxRestUtils
import Utils.IxLoadTestSettings as TestSettings
import inspect


#### TEST CONFIG
testSettings = TestSettings.IxLoadTestSettings()
# testSettings.gatewayServer = "machine_ip_address"     # TODO - to be changed by user if he wants to run remote
testSettings.ixLoadVersion = ""                         # TODO - to be changed by user, by default will run on the latest installed version
testSettings.chassisList = ['chassisIpOrHostName']      # TODO - to be changed by user

location=inspect.getfile(inspect.currentframe())

testSettings.portListPerCommunity = {
                                        "Traffic1@Network1" : [(1,2,1)],
                                        "Traffic2@Network2" : [(1,2,5)]
                                    }

kStatsToDisplayDict =   {
                            # format: { statSource : [stat name list] }
                            "VideoClient": ["VoD Streams Played", "RTSP Connections"],
                            "VideoServer": ["Total Streams Playing", "Total Streaming Bit Rate"]
                        }

kCommunities = [
    # format: {option1: value1, option2: value2}
    {}, # default community with no options
    {"tcpAccelerationAllowedFlag": True}  # community with tcpAccelerationAllowedFlag set to True
]

kActivities = {
    # format: {communityName: [activityProtocolAndType1, activityProtocolAndType2]}
    'Traffic1@Network1': ['Video Client'],
    'Traffic2@Network2': ['Video Server']
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

    IxLoadUtils.log('Adding IPTV command to IPTV Video Client...')
    iptvCommandOptions = {'commandType': 'PlayMediaCommand', 'symServerIP': 'Traffic2_IPTV_VideoServer1:554', 'media': 'Stream0'}
    IxLoadUtils.IPTVUtils.addIPTVCommand(connection, sessionUrl, 'Traffic1@Network1', 'IPTV_VideoClient1', iptvCommandOptions)
    IxLoadUtils.log('Command added to IPTV Video Client.')

    IxLoadUtils.log("Clearing chassis list...")
    IxLoadUtils.clearChassisList(connection, sessionUrl)
    IxLoadUtils.log("Chassis list cleared.")

    IxLoadUtils.log("Adding chassis %s..." % (testSettings.chassisList))
    IxLoadUtils.addChassisList(connection, sessionUrl, testSettings.chassisList)
    IxLoadUtils.log("Chassis added.")

    IxLoadUtils.log("Assigning new ports...")
    IxLoadUtils.assignPorts(connection, sessionUrl, testSettings.portListPerCommunity)
    IxLoadUtils.log("Ports assigned.")

    IxLoadUtils.log("Saving repository %s..." % (IxLoadUtils.getRxfName(connection, location)))
    IxLoadUtils.saveRxf(connection, sessionUrl, IxLoadUtils.getRxfName(connection, location))
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
