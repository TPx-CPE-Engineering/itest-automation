#!/usr/bin/env python3
from login.operator_login import velocloud_api as vc_api
from my_velocloud import functions as my_vc


# Globals
EDGE_ID = None
ENTERPRISE_ID = None


def set_globals(edge_id, enterprise_id) -> None:
    global EDGE_ID, ENTERPRISE_ID
    EDGE_ID = int(edge_id)
    ENTERPRISE_ID = int(enterprise_id)


def main():
    edge_firewall = my_vc.get_module_from_edge_specific_profile(module_name='firewall', edge_id=8, enterprise_id=1)
    print(edge_firewall)


if __name__ == '__main__':
    main()
