#!/usr/bin/env python
from my_silverpeak.base_edge import SPBaseEdge


class SPEdge(SPBaseEdge):
    def __init__(self, edge_id, enterprise_id, ssh_port):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port, auto_operator_login=True)
        self.ssh_rule = None

EDGE: SPEdge


def set_globals(edge_id, enterprise_id, ssh_port):
    """
    Set the globals for the test case.
    Remember to set the type in here
    """

    global EDGE
    EDGE = SPEdge(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=str(ssh_port))


def is_ssh_rule_present() -> None:
    """
    Checks if SSH Inbound Port Forwarding Rule is in the Silverpeak Appliance
    It looks for a rule that has ..
    1. 'tcp' has its protocol
    2. Its destination port is equal to global SSH_PORT
    3. The string 'itest' is in the rule's comments
    """

    d = {'is_ssh_rule_present': None}

    url = EDGE.api.base_url + '/portForwarding/' + EDGE.edge_id
    res = EDGE.api._get(EDGE.api.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    for rule in inbound_port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == EDGE.ssh_port and 'itest' in rule['comment'].lower():
            d['is_ssh_rule_present'] = 'yes'
            print(d)
            return

    d['is_ssh_rule_present'] = 'no'
    print(d)
    return


def remove_ssh_rule():
    """
    Removes SSH Inbound Port Forwarding Rule from Silverpeak Appliance
    It removes the SSH rule that has..
    1. 'tcp' has its protocol
    2. Its destination port is equal to global SSH_PORT
    3. The string 'itest' is in the rule's comments
    """

    url = EDGE.api.base_url + '/portForwarding/' + EDGE.edge_id
    res = EDGE.api._get(EDGE.api.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    for rule in inbound_port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == EDGE.ssh_port and 'itest' in rule['comment'].lower():
            EDGE.ssh_rule = rule
            inbound_port_forwarding_rules.remove(rule)

    url = EDGE.api.base_url + '/appliance/rest/' + EDGE.edge_id + '/portForwarding2'
    res = EDGE.api._post(session=EDGE.api.session, url=url, json=inbound_port_forwarding_rules)

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

    url = EDGE.api.base_url + '/portForwarding/' + EDGE.edge_id
    res = EDGE.api._get(EDGE.api.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    inbound_port_forwarding_rules.append(EDGE.ssh_rule)

    url = EDGE.api.base_url + '/appliance/rest/' + EDGE.edge_id + '/portForwarding2'
    res = EDGE.api._post(session=EDGE.api.session, url=url, json=inbound_port_forwarding_rules)

    if res.error:
        d = {'error': res.error}
        print(d)
    else:
        d = {'error': None}
        print(d)


if __name__ == '__main__':
    set_globals(edge_id="18.NE", enterprise_id=None, ssh_port="2203")
