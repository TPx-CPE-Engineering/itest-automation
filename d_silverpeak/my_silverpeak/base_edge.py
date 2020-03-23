from my_silverpeak import operator_login

"""
Base Edge template for Silverpeak automation
"""


class SPBaseEdge:
    def __init__(self, edge_id, enterprise_id, ssh_port, auto_operator_login=True):
        self.edge_id = edge_id
        self.enterprise_id = enterprise_id
        self.ssh_port = ssh_port
        self.api = None
        self.cpe_lan_ip = None

        if auto_operator_login:
            self.api = operator_login.login()

    def get_cpe_lan_ip(self):
        """
        Get the CPE's LAN IP (sitting behind Silverpeak Edge) by looking at the port forwarding rules and looking for port, protocol, and comment
        :return: CPE LAN IP or an empty str
        """

        # Check if cpe_lan_ip is already set
        if self.cpe_lan_ip:
            return self.cpe_lan_ip

        # Else find cpe_lan_ip
        # Get Port Forwarding Rules
        url = self.api.base_url + '/portForwarding/' + self.edge_id
        res = self.api._get(session=self.api.session, url=url, headers=None, timeout=10)
        port_forwarding_rules = res.data

        # Locate the SSH Port Forwarding Rules based on it its protocol destination port and it has itest in the comments
        for rule in port_forwarding_rules:
            if rule['protocol'] == 'tcp' and rule['destPort'] == self.ssh_port and 'itest' in rule['comment'].lower():
                return rule['targetIp']

        # If rule is not found then raise a KeyError
        raise KeyError("A SSH Inbound Forwarding Rule with Protocol = TCP, Destination Port = {}, and string 'itest' in the Comment was not found.".format(
            self.ssh_port))