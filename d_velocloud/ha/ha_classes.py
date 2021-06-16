from my_velocloud.VelocloudEdge import VeloCloudEdge
import json
from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi


class HAVeloCloudEdge(VeloCloudEdge):
    def __init__(self, edge_id, enterprise_id):
        super().__init__(edge_id, enterprise_id)
        self.initial_active_device_serial_number = None
        self.initial_ha_device_serial_number = None

    def check_for_ha_going_active_in_edge_events(self, start_interval):
        # print(f"Start Interval: {start_interval}")
        events = self.get_enterprise_events(start_interval=start_interval)

        response = {'HA_GOING_ACTIVE Present': False}
        for event in events['data']:
            if event['event'] == 'HA_GOING_ACTIVE':
                response['HA_GOING_ACTIVE Present'] = True

        print(response)
        print(json.dumps(events['data'], indent=2))

    def get_active_device_serial_number(self):
        edge_info = self.get_edge()

        # Depending on the device family, we either collect the first or last 3 characters
        models_to_get_last_three_serial_numbers = ['EDGE5X0', 'EDGE8X0']

        response = {"serial number": None,
                    "switch serial number": None}

        self.initial_active_device_serial_number = edge_info["serialNumber"]

        if edge_info['deviceFamily'] in models_to_get_last_three_serial_numbers:
            response["serial number"] = edge_info["serialNumber"]
            response["switch serial number"] = edge_info["serialNumber"][-3:]
            return response
        else:
            response["serial number"] = edge_info["serialNumber"]
            response["switch serial number"] = edge_info["serialNumber"][:3]
            return response

    def get_ha_device_serial_number(self):
        edge_info = self.get_edge()

        # Depending on the device family, we either collect the first or last 3 characters
        models_to_get_last_three_serial_numbers = ['EDGE5X0', 'EDGE8X0']

        response = {"ha serial number": None,
                    "switch serial number": None}

        self.initial_ha_device_serial_number = edge_info['haSerialNumber']

        if edge_info['deviceFamily'] in models_to_get_last_three_serial_numbers:
            response["ha serial number"] = edge_info["haSerialNumber"]
            response["switch serial number"] = edge_info["haSerialNumber"][-3:]
            return response
        else:
            response["ha serial number"] = edge_info["haSerialNumber"]
            response["switch serial number"] = edge_info["haSerialNumber"][:3]
            return response

    def check_if_active_ha_serial_numbers_swapped(self):
        edge_info = self.get_edge()
        active_serial_number = edge_info['serialNumber']
        ha_serial_number = edge_info['haSerialNumber']

        # When tests begins
        # active device serial number = 90P
        # ha device serial number = J4P
        # After tests, they should have been swapped
        # active device serial number = J4P
        # ha device serial number = 90P
        # verify this happened

        if self.initial_active_device_serial_number == ha_serial_number and \
                self.initial_ha_device_serial_number == active_serial_number:
            print({"swap": "successful"})
        else:
            print({"swap": "failed"})

        print({
            "initial active serial number": self.initial_active_device_serial_number,
            "initial ha serial number": self.initial_ha_device_serial_number,
            "current active serial number": active_serial_number,
            "current ha serial number": ha_serial_number
        })