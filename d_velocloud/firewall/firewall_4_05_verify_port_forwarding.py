from velocloud.models import *
from my_velocloud.BaseEdge import BaseEdge


class Edge(BaseEdge):

    def __init__(self, edge_id: int, enterprise_id: int, ssh_port: int):
        super().__init__(edge_id=edge_id, enterprise_id=enterprise_id, ssh_port=ssh_port)
        self.cpe_ssh_port_forwarding_rule = None


# Global
EDGE: Edge


def set_globals(edge_id, enterprise_id, ssh_port) -> None:
    global EDGE
    EDGE = Edge(edge_id=int(edge_id), enterprise_id=int(enterprise_id), ssh_port=int(ssh_port))


def is_ssh_rule_present() -> None:
    """
    Check if edge contains the SSH Port Forwarding rule

    """

    d = {'is_ssh_rule_present': None}

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    # Loop through inbound rules and check for a rule that has the following conditions:
    # 1. 'itest' is in the rule's name
    # 2. Rule's WAN Ports match ssh_port
    # 3. Rule's LAN Port is 22
    # If there is a rule with the above conditions, ssh rule exists
    # else ssh rule does not exists
    for rule in firewall_module.data['inbound']:
        if 'itest' in rule['name'].lower() and rule['action']['nat']['lan_port'] == 22 and rule['match'][
           'dport_high'] == EDGE.ssh_port and rule['match']['dport_low'] == EDGE.ssh_port:
            d['is_ssh_rule_present'] = 'yes'
            print(d)
            return

    d['is_ssh_rule_present'] = 'no'
    print(d)
    return


def remove_ssh_rule() -> None:
    """
    Remove SSH rule

    Removes SSH
    SSH rule is saved in EDGE.cpe_ssh_port_forwarding rule then removed from the Edge firewall rules.
    """

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    for rule in firewall_module.data['inbound']:
        if 'itest' in rule['name'].lower() and rule['action']['nat']['lan_port'] == 22 and rule['match'][
           'dport_high'] == EDGE.ssh_port and rule['match']['dport_low'] == EDGE.ssh_port:
            EDGE.cpe_ssh_port_forwarding_rule = rule
            firewall_module.data['inbound'].remove(rule)

    param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=EDGE.enterprise_id,
                                                   update=firewall_module)

    res = EDGE.api.configurationUpdateConfigurationModule(param)
    print(res)


def add_ssh_rule() -> None:
    """
    Add SSH rule back into the edge

    SSH rule is saved in the SSH_RULE global variable when it was removed
    """

    if not EDGE.cpe_ssh_port_forwarding_rule:
        print('No rule saved. Please add CPE ssh port forwarding rule manually.')
        return

    # Get Edge's firewall module
    firewall_module: ConfigurationModule = EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    firewall_module.data['inbound'].append(EDGE.cpe_ssh_port_forwarding_rule)

    param = ConfigurationUpdateConfigurationModule(id=firewall_module.id, enterpriseId=EDGE.enterprise_id,
                                                   update=firewall_module)

    res = EDGE.api.configurationUpdateConfigurationModule(param)
    print(res)


if __name__ == "__main__":
    set_globals(edge_id=4, enterprise_id=1, ssh_port=2202)
    is_ssh_rule_present()
