from my_velocloud.BaseEdge import BaseEdge
import time
from datetime import datetime

"""
Written by: juan.brena@tpx.com
Date: 2/21/2020

Revised:

Test Case #1
Test Case: Downgrade edge/customer
Expected Results: Downgrade successful
Usage: Downgrade edge using VCO (Configure > Select Device > Actions > Assign Operator Profile).
Monitor progress in Even log (Monitor > Events).

Test Case #2
Test Case: Upgrade edge/customer
Expected Results: Upgrade successful
Usage: Upgrade edge using VCO (Configure > Select Device > Actions > Assign Operator Profile).
Monitor progress in Event log (Monitor > Events).
"""

# Used to get events from this epoch
EPOCH = int()


class UpgradeDowngradeEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
        self.current_operator_profile = self.get_current_operator_profile()
        self.downgrade_operator_profile = self.get_downgrade_operator_profile()

    def get_downgrade_operator_profile(self):
        """
        Get operator profile to downgrade to based on software version
        """
        # Find which operator profile to downgrade to
        cpe_operator_profiles = self.get_cpe_operator_profiles()

        for profile in cpe_operator_profiles:
            if self.software_version_compare(v1=self.current_operator_profile['software version'],
                                             v2=profile['software version']) == 1:
                return profile

    def get_current_operator_profile(self):
        """
        Get operator profile edge is on based on it's software version
        """

        current_software_version = self.get_software_version()
        cpe_operator_profiles = self.get_cpe_operator_profiles()

        # Look through CPE Operator Profiles and find the one with the current software version in the name.
        for profile in cpe_operator_profiles:
            if current_software_version in profile['name']:
                return profile

    def get_software_version(self) -> str:
        """
        Returns Edge's current software version
        """

        # Set API parameters for EnterpriseGetEnterpriseEdges
        param = {'enterpriseId': self.enterprise_id, '_with': ['configuration']}

        # Perform API call
        enterprise_edges = self.api.enterpriseGetEnterpriseEdges(param)

        # Filter through all of Enterprise Edges and return self software version
        for edge in enterprise_edges:
            if edge.id == self.id:
                return edge.softwareVersion

    def get_cpe_operator_profiles(self) -> []:
        """
        Returns VCO's CPE only operator profiles an Edge can upgrade/downgrade to

        By CPE-only the operator profile name must start with a Digit and contain 'CPE' string within the name
        Example name: '1.2.0 CPE Operator Profile'
        """

        # Perform API Call to get all VCO's operator profiles
        operator_profiles = self.api.networkGetNetworkConfigurations({})

        # We only want CPE's operator profiles
        cpe_operator_profiles = []
        for profile in operator_profiles:
            if profile.name[0].isdigit() and profile.name.split(' ')[1] == 'CPE':
                software_version = profile.name.split()
                software_version = software_version[0]
                d = {'name': profile.name, 'id': profile.id, 'version': profile.version,
                     'software version': software_version}
                cpe_operator_profiles.append(d)

        # Sort them by version
        cpe_operator_profiles = sorted(cpe_operator_profiles, key=lambda i: i['version'], reverse=True)

        return cpe_operator_profiles

    def upgrade_edge(self):
        """
        Upgrades Edge back to its operator profile before being downgraded
        """

        # Set API parameters
        d = {"Upgrading Edge to": self.current_operator_profile['name']}
        print(d)

        # Set api parameters
        param = {'edgeId': self.id, 'enterpriseId': self.enterprise_id,
                 'configurationId': self.current_operator_profile['id']}

        # Execute Upgrade api call
        res = EDGE.api.edgeSetEdgeOperatorConfiguration(param)

        # Print results
        print(res)

    def downgrade_edge(self):
        """
        Downgrades Edge to a lower version than its current operator profile version
        """

        d = {'Downgrading Edge to': self.downgrade_operator_profile['name']}
        print(d)

        # Set api parameters
        param = {'edgeId': self.id, 'enterpriseId': self.enterprise_id,
                 'configurationId': self.downgrade_operator_profile['id']}

        # Execute Downgrade api call
        res = EDGE.api.edgeSetEdgeOperatorConfiguration(param)

        # Print results
        print(res)

    def restore_edge_to_original_firmware(self):
        """
        Restores Edge to its orignal firmware version
        """
        print({"Restoring Edge to": self.current_operator_profile['name']})

        # Set api parameters
        param = {'edgeId': self.id, 'enterpriseId': self.enterprise_id,
                 'configurationId': self.current_operator_profile['id']}

        # Execute Upgrade api call
        res = EDGE.api.edgeSetEdgeOperatorConfiguration(param)

        # Print results
        print(res)

    def check_for_edge_downgrade_upgrade_events(self):
        """
        Checks if 4 events occurred and no error severity event occurred in the Edge's events log

        Checking if the following events occurred:
            Configuration Applied
            Software Update
            Edge Restart
            Edge online
        and checking if no error severity event occurred
        """

        # Set param for events api call
        param = {'edgeId': self.id, 'enterpriseId': self.enterprise_id, 'interval': {'start': EPOCH}}

        # Get Edge events through api call
        edge_events = EDGE.api.eventGetEnterpriseEvents(param)

        # Search through the event messages and look for 4 specific events
        configuration_applied = False
        software_update = False
        edge_restart = False
        edge_online = False
        event_messages = []
        for event in reversed(edge_events.data):
            event_messages.append(event.message)
            if "Applied new configuration for imageUpdate" in event.message:
                configuration_applied = True
                continue
            if "Installed downloaded software version" in event.message:
                software_update = True
                continue
            if "Edge is restarting into new software version" in event.message:
                edge_restart = True
                continue
            if "Management Daemon Started, version" in event.message:
                edge_online = True
                continue

        # Search through the events and look for any severity errors
        error_severity_found = False
        for event in reversed(edge_events.data):
            if event.severity == 'Error':
                error_severity_found = True

        # Print results
        d = {"Edge Upgrade Events Status": None}
        if not error_severity_found and configuration_applied and software_update and edge_restart and edge_online:
            d["Edge Upgrade Events Status"] = 'Passed'
        else:
            d["Edge Upgrade Events Status"] = 'Failed'

        print(d)
        print({"All Event Messages since {}".format(get_datetime_str_from_epoch()): event_messages})

    def print_firmware_relevant_edge_events(self):
        """
        Prints any edge event messages with the software version in it
        """
        edge_software_version = self.get_software_version()

        # Set param for events api call
        param = {'edgeId': self.id, 'enterpriseId': self.enterprise_id, 'interval': {'start': EPOCH}}

        # call events api
        edge_events = EDGE.api.eventGetEnterpriseEvents(param)

        # Print event messages
        messages = []
        for event in edge_events.data:
            if edge_software_version in event.message:
                messages.append(event.message + '$')

        # Remove the '$' from the last item in the list
        messages[-1] = messages[-1][:-1]

        print({"Event Messages": messages})

    @staticmethod
    def software_version_compare(v1, v2):
        """
        Method to compare two software versions.
        Return  1 if v2 is smaller,
                -1 if v1 is smaller,,
                0 if equal
        """
        # Check for hot-patches
        if '-' in v1:
            hyphen_index = v1.index('-')
            v1 = v1[:hyphen_index]

        if '-' in v2:
            hyphen_index = v2.index('-')
            v2 = v2[:hyphen_index]

        # This will split both the versions by '.'
        arr1 = v1.split(".")
        arr2 = v2.split(".")

        # Initializer for the version arrays
        i = 0

        # We have taken into consideration that both the
        # versions will contains equal number of delimiters
        while i < len(arr1):

            # Version 2 is greater than version 1
            if int(arr2[i]) > int(arr1[i]):
                return -1

            # Version 1 is greater than version 2
            if int(arr1[i]) > int(arr2[i]):
                return 1

            # We can't conclude till now
            i += 1

        # Both the versions are equal
        return 0


EDGE: UpgradeDowngradeEdge


def create_edge(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = UpgradeDowngradeEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def print_edge_software_version():
    d = {"Edge software version": EDGE.get_software_version()}
    print(d)


def print_available_cpe_operator_profiles():
    d = {"CPE operator profiles": EDGE.get_cpe_operator_profiles()}
    print(d)


def upgrade_edge():
    global EPOCH
    EPOCH = int(round(time.time() * 1000))
    EDGE.upgrade_edge()


def downgrade_edge():
    global EPOCH
    EPOCH = int(round(time.time() * 1000))
    EDGE.downgrade_edge()


def restore_edge_to_original_firmware():
    global EPOCH
    EPOCH = int(round(time.time() * 1000))
    EDGE.restore_edge_to_original_firmware()


def check_for_edge_downgrade_upgrade_events():
    EDGE.check_for_edge_downgrade_upgrade_events()


def print_firmware_relevant_edge_events():
    EDGE.print_firmware_relevant_edge_events()


def get_datetime_str_from_epoch():
    return datetime.fromtimestamp(EPOCH/1000).strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    create_edge(edge_id='1', enterprise_id='1', ssh_port='2201')
