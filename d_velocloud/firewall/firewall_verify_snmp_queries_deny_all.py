#!/usr/bin/env python3
from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge


class FirewallSNMPEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)


# Globals
EDGE: FirewallSNMPEdge


def set_globals(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = BaseEdge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


if __name__ == '__main__':
    set_globals(edge_id=4, enterprise_id=1, ssh_port=2201)