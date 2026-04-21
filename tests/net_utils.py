import yaml
from netmiko import ConnectHandler, ReadTimeout
from jinja2 import Template

with open('config.yaml', 'r') as f:
    inventory = yaml.safe_load(f)

def push_config(template):
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            output = net_connect.send_config_set(template, read_timeout=50)
            print(output)
    except Exception as e:
        print(f'FAILED TO CONNECT! : {e}')

def run_commands(cmd):
    with ConnectHandler(**inventory['router']) as net_connect:
        return net_connect.send_command(cmd)






























































