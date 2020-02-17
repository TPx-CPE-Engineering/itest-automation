from velocloud.models import *
from my_velocloud.operator_login import velocloud_api as api
from my_velocloud.base_edge import BaseEdge


class DNSBaseEdge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)