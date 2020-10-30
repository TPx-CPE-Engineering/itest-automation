from my_silverpeak.base_edge import SPBaseEdge


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)
        self.ssh_rule = None


DUT_EDGE: SPEdge
CPE_SSH_PORT_FORWARDING_RULE: dict


def create_edge(edge_id, enterprise_id, ssh_port):
    """
    Set the globals for the test case.
    Remember to set the type in here
    """

    global DUT_EDGE
    DUT_EDGE = SPEdge(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=str(ssh_port))


def remove_ssh_rule():
    """
    Removes SSH Inbound Port Forwarding Rule from Silverpeak Appliance
    It removes the SSH rule that has..
    1. 'tcp' has its protocol
    2. Its destination port is equal to global SSH_PORT
    3. The string 'itest' is in the rule's comments
    """
    global CPE_SSH_PORT_FORWARDING_RULE

    url = DUT_EDGE.api.base_url + '/portForwarding/' + DUT_EDGE.edge_id
    res = DUT_EDGE.api._get(DUT_EDGE.api.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    for rule in inbound_port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == DUT_EDGE.ssh_port and 'itest' in rule['comment'].lower():
            CPE_SSH_PORT_FORWARDING_RULE = rule
            inbound_port_forwarding_rules.remove(rule)

    url = DUT_EDGE.api.base_url + '/appliance/rest/' + DUT_EDGE.edge_id + '/portForwarding2'
    res = DUT_EDGE.api._post(session=DUT_EDGE.api.session, url=url, json=inbound_port_forwarding_rules)

    if res.error:
        d = {'error': res.error}
        print(d)
        return
    else:
        d = {'error': None}
        print(d)
        return


def add_ssh_rule():
    """
    Add SSH Inbound Port Forwarding Rule to the Silverpeak Appliance
    It adds the once removed SSH rule back into the Silverpeak Appliance.
    Before deleting, the rule is saved in the global SSH_RULE variable so we can
    easily add it back.
    """

    url = DUT_EDGE.api.base_url + '/portForwarding/' + DUT_EDGE.edge_id
    res = DUT_EDGE.api._get(DUT_EDGE.api.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    if not inbound_port_forwarding_rules:
        inbound_port_forwarding_rules = []

    inbound_port_forwarding_rules.append(CPE_SSH_PORT_FORWARDING_RULE)

    url = DUT_EDGE.api.base_url + '/appliance/rest/' + DUT_EDGE.edge_id + '/portForwarding2'
    res = DUT_EDGE.api._post(session=DUT_EDGE.api.session, url=url, json=inbound_port_forwarding_rules)

    if res.error:
        d = {'error': res.error}
        print(d)
    else:
        d = {'error': None}
        print(d)


if __name__ == '__main__':
    add_ssh_rule()
