from my_silverpeak.OSPFEdge import OSPFEdge
import json


def create_edge(edge_id, enterprise_id):
    print('todo')


if __name__ == '__main__':
    Edge = OSPFEdge(edge_id='18.NE', enterprise_id=None, ssh_port=None)
    res = Edge.api.get_ospf_state_neighbors(applianceID=Edge.edge_id)
    print(res)