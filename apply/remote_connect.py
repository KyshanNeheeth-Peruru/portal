import paramiko
import os
from pathlib import Path
import environ
from paramiko import AuthenticationException

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


class RemoteConnect:
    def __init__(self):
        self.host = env("REMOTE_HOST_d301")
        self.conn_handle = None
        self.username = env("REMOTE_USER")
        self.userpass = env("REMOTE_PASSWORD")
        self.__connect()

    def __connect(self):
        try:
            self.conn_handle = paramiko.client.SSHClient()
            self.conn_handle.load_system_host_keys()
            self.conn_handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.conn_handle.connect(self.host, 22, self.username, self.userpass)
        except AuthenticationException as error:
            print('Authentication Failed: Please check your username and password')
        finally:
            print("Connection handle open for " + self.host)
            return self.conn_handle

    def disconnect(self):
        self.conn_handle.close()

    def execute_command(self, command):
        if self.conn_handle == None:
            self.conn_handle = self.__connect()
        stdin, stdout, stderr = self.conn_handle.exec_command(command)
        status = stdout.channel.recv_exit_status()
        if status == 0:
            return stdout.read()
        else:
            return -1


# if __name__ == '__main__':
#     rc = RemoteConnect()
#     rc.execute_command("sudo python3 /srv/home_directory.py -username karthik3 -uid 13810")
#     rc.execute_command("sudo python3 /srv/course_directory.py -user karthik3 -course cs624 -sem f22 -prof ming")
#     rc.execute_command("sudo python3 /srv/course_directory.py -user karthik3 -course cs630 -sem f22 -prof marc")