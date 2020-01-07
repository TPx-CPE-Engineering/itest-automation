#!/usr/bin/env python
from silverpeak import *

# Login
sp = Silverpeak(user='juan.brena', user_pass='1Maule1!', sp_server='cpesp.lab-sv.telepacific.com', disable_warnings=True)

# Globals
EDGE_ID = None
ENTERPRISE_ID = None
SSH_PORT = None
SSH_RULE = None


def set_globals(edge_id, enterprise_id, ssh_port):
    """
    Set the globals for the test case.
    Remember to set the type in here
    """
    global EDGE_ID, ENTERPRISE_ID, SSH_PORT
    EDGE_ID = edge_id
    ENTERPRISE_ID = enterprise_id
    SSH_PORT = str(ssh_port)


def is_ssh_rule_present() -> None:
    """
    Checks if SSH Inbound Port Forwarding Rule is in the Silverpeak Appliance
    It looks for a rule that has ..
    1. 'tcp' has its protocol
    2. Its destination port is equal to global SSH_PORT
    3. Its translated port is equal to global SSH_PORT
    4. The word 'itest' is in the rule's comments
    """

    global EDGE_ID, SSH_PORT

    d = {'is_ssh_rule_present': None}

    url = sp.base_url + '/portForwarding/' + EDGE_ID
    res = sp._get(sp.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    for rule in inbound_port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == SSH_PORT and rule['targetPort'] == SSH_PORT and 'itest' \
                in rule['comment'].lower():
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
    3. Its translated port is equal to global SSH_PORT
    4. The word 'itest' is in the rule's comments
    """

    global EDGE_ID, SSH_PORT, SSH_RULE

    url = sp.base_url + '/portForwarding/' + EDGE_ID
    res = sp._get(sp.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    for rule in inbound_port_forwarding_rules:
        if rule['protocol'] == 'tcp' and rule['destPort'] == SSH_PORT and rule['targetPort'] == SSH_PORT and 'itest' \
                in rule['comment'].lower():
            SSH_RULE = rule
            inbound_port_forwarding_rules.remove(rule)

    url = sp.base_url + '/appliance/rest/' + EDGE_ID + '/portForwarding2'
    res = sp._post(session=sp.session, url=url, json=inbound_port_forwarding_rules)

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
    global EDGE_ID, SSH_RULE

    url = sp.base_url + '/portForwarding/' + EDGE_ID
    res = sp._get(sp.session, url=url, headers=None, timeout=10)
    inbound_port_forwarding_rules = res.data

    inbound_port_forwarding_rules.append(SSH_RULE)

    url = sp.base_url + '/appliance/rest/' + EDGE_ID + '/portForwarding2'
    res = sp._post(session=sp.session, url=url, json=inbound_port_forwarding_rules)

    if res.error:
        d = {'error': res.error}
        print(d)
        return
    else:
        d = {'error': None}
        print(d)
        return
