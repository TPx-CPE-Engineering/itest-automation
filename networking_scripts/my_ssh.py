import paramiko


def ssh_connect(host:str, port:int, username:str, password:str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port, username, password)
        print('SSH Connection Successful')
        return ssh
    except TimeoutError:
        print('Timeout Error')
