from my_velocloud.VelocloudEdge import VeloCloudEdge
from ix_load.Modules.IxL_RestApi import *
import json
from d_ixia.ix_load.Modules.MyIxLoadAPI import IxLoadApi
import time

DUT_EDGE: VeloCloudEdge
IxLoad = IxLoadApi()
EPOCH = int()


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE, EPOCH
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)
    EPOCH = int(round(time.time() * 1000))
    return DUT_EDGE, EPOCH

if __name__ == '__main__':
    edge, epoch = create_edge(edge_id=246, enterprise_id=1)
    print(edge)