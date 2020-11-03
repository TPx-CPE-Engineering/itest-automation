import paramiko


def ssh_connect(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port, username, password)
        print('SSH Connection Successful')
    except TimeoutError:
        print('Timeout Error')
