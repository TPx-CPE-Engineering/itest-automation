#!/usr/bin/env python3
import velocloud
from velocloud.models import *
from velocloud.rest import ApiException

# Operator Login
client = velocloud.ApiClient(host="cpevc.lab-sv.telepacific.com")
api = velocloud.AllApi(api_client=client)

try:
    client.authenticate(username="juan.brena@tpx.com", password="1Maule1!", operator=True)
except ApiException as login_exception:
    print(login_exception)
    exit()

# Globals
EDGE_ID = None
ENTERPRISE_ID = None


def main():
    print('testing')


if __name__ == '__main__':
    main()
