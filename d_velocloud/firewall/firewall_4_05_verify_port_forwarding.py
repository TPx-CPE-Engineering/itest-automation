import paramiko
from my_velocloud.VelocloudEdge import VeloCloudEdge


# Global
# EDGE: Edge
DUT_EDGE: VeloCloudEdge
CPE_SSH_PORT_FORWARDING_RULE: dict


def create_edge(edge_id, enterprise_id, ssh_port):
    global DUT_EDGE
    DUT_EDGE = VeloCloudEdge(edge_id=edge_id,
                             enterprise_id=enterprise_id,
                             cpe_ssh_port=ssh_port)


def remove_ssh_rule() -> None:
    """
    Remove SSH rule

    Removes SSH
    SSH rule is saved in EDGE.cpe_ssh_port_forwarding rule then removed from the Edge firewall rules.
    """
    global CPE_SSH_PORT_FORWARDING_RULE

    # Get Edge's firewall module
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    for rule in firewall_module['data']['inbound']:
        if 'itest' in rule['name'].lower() and rule['action']['nat']['lan_port'] == 22 and rule['match'][
           'dport_high'] == DUT_EDGE.cpe_ssh_port and rule['match']['dport_low'] == DUT_EDGE.cpe_ssh_port:
            CPE_SSH_PORT_FORWARDING_RULE = rule
            firewall_module['data']['inbound'].remove(rule)

    print(DUT_EDGE.update_configuration_module(module=firewall_module))


def add_ssh_rule() -> None:
    """
    Add SSH rule back into the edge

    SSH rule is saved in the SSH_RULE global variable when it was removed
    """

    # Get Edge's firewall module
    firewall_module = DUT_EDGE.get_module_from_edge_specific_profile(module_name='firewall')

    firewall_module['data']['inbound'].append(CPE_SSH_PORT_FORWARDING_RULE)

    print(DUT_EDGE.update_configuration_module(module=firewall_module))


def ssh_connect(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port, username, password)
        print('SSH Connection Successful')
    except TimeoutError:
        print('Timeout Error')


if __name__ == "__main__":
    create_edge(edge_id=245, enterprise_id=1, ssh_port=2201)
    import time
    remove_ssh_rule()
    time.sleep(30)
    add_ssh_rule()