from my_velocloud.VelocloudEdge import LANSideNatVelocloudEdge

DUT_EDGE: LANSideNatVelocloudEdge


def add_lan_side_nat_rule():

    nat_rule = {
        "insideCidrIp": "10.0.0.0",
        "insideCidrPrefix": 32,
        "insidePort": -1,
        "outsideCidrIp": "192.168.0.0",
        "outsideCidrPrefix": 24,
        "outsidePort": -1,
        "type": "source",
        "description": "Added by iTest",
        "srcCidrIp": "",
        "srcCidrPrefix": "",
        "destCidrIp": "",
        "destCidrPrefix": "",
        "insideNetmask": "255.255.255.255",
        "outsideNetmask": "255.255.255.0",
        "srcNetmask": "",
        "destNetmask": ""
    }

    print(DUT_EDGE.add_nat_rules_to_segment(segment_name='Voice', rules=[nat_rule], dual_rules=[]))


def delete_all_nat_rules():
    print(DUT_EDGE.delete_all_nat_rules_from_segment(segment_name='Voice'))


def create_edge(edge_id, enterprise_id):
    global DUT_EDGE
    DUT_EDGE = LANSideNatVelocloudEdge(edge_id=edge_id, enterprise_id=enterprise_id)


if __name__ == '__main__':
    create_edge(edge_id=245, enterprise_id=1)
    delete_all_nat_rules()