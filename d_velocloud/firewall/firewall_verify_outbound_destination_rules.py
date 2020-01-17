#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge

# Globals
EDGE = None


class Edge(BaseEdge):
    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)


def set_globals(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = Edge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=ssh_port)


def main():
    set_globals(edge_id=4, enterprise_id=1, ssh_port=0)
    edge_firewall = EDGE.get_module_from_edge_specific_profile(module_name='firewall')
    print(edge_firewall)


if __name__ == '__main__':
    main()
