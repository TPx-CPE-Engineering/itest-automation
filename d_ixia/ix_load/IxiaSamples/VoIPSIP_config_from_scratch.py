import Utils.IxLoadUtils as IxLoadUtils
import Utils.IxRestUtils as IxRestUtils
import Utils.IxLoadTestSettings as TestSettings
import inspect, os
from collections import OrderedDict


#### TEST CONFIG
testSettings = TestSettings.IxLoadTestSettings()
# testSettings.gatewayServer = "machine_ip_address"     # TODO - to be changed by user if he wants to run remote
testSettings.ixLoadVersion = ""                         # TODO - to be changed by user, by default will run on the latest installed version
testSettings.chassisList = ['chassisIpOrHostName']      # TODO - to be changed by user

location = inspect.getfile(inspect.currentframe())

testSettings.portListPerCommunity = {
                                        "Traffic1@Network1" : [(1,7,1)],
                                        "Traffic2@Network2" : [(1,7,5)]
                                    }

kStatsToDisplayDict =   {
                            # format: { statSource : [stat name list] }
                            "RTP(VoIPSip)": ["Successful Records", "Functions Disconnected"],
                            "Flow(VoIPSip)": ["Successful Channels", "Active Channels"]
                        }

kCommunities = [
    # format: {option1: value1, option2: value2}
    {}, # default community with no options
    {"tcpAccelerationAllowedFlag": True}  # community with tcpAccelerationAllowedFlag set to True
]

kActivities = OrderedDict([
    # format: {communityName: [activityProtocolAndType1, activityProtocolAndType2]}
    ('Traffic1@Network1', ['VoIP Peer']),
    ('Traffic2@Network2', ['VoIP Peer'])
])

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

    IxLoadUtils.log('Editing scenario settings on VoIPSIP peers...')
    rootFolder = os.getcwd()
    tstFilePath = '/'.join([rootFolder, 'TestScenario1.tst']) # TODO - this will have to be edited by the user
    voipsipCommandOptions = {"scenarioFile": tstFilePath}
    IxLoadUtils.VoipPeerUtils.changeScenarioSettings(connection, sessionUrl, 'Traffic1@Network1', 'VoIPSipPeer1', voipsipCommandOptions)
    IxLoadUtils.VoipPeerUtils.changeScenarioSettings(connection, sessionUrl, 'Traffic2@Network2', 'VoIPSipPeer2', voipsipCommandOptions)

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
