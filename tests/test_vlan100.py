from netmiko import ConnectHandler
from jinja2 import Template
import re
import time
import pytest
import yaml
import subprocess
Pc_Ip = '192.168.100.254'
Neighbor_Ip = '192.168.100.2'

with open('config.yaml', 'r') as f:
    inventory = yaml.safe_load(f)

with open('templates/vlan_config.j2', 'r') as v:
    template = (Template(v.read()).render()).splitlines()

def push_config():
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            output = net_connect.send_config_set(template, read_timeout=30)
            print(output)
    except Exception as e:
        print(f'FAILED TO CONNECT! : {e}')

def run_commands(cmd):
    with ConnectHandler(**inventory['router']) as net_connect:
        cmd_output = net_connect.send_command(cmd)
        return cmd_output
    
    return matches

def test_vlan_interface_seperated():
    push_config()
    brctl = run_commands('brctl show')
    assert 'portB.100' in brctl, f'FAILED: PortB.100 is not in brctl'

def test_vlan_link_up():
    link = run_commands('ip link show | grep portB.100')
    assert 'state UP' in link, f'FAILED: State is DOWN'

def test_ping_connectivity():
    result = subprocess.run(['ping', '-c', '5', Neighbor_Ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ping_output = result.stdout
    match = re.search(r'(\d+)% packet loss', ping_output)
    loss = int(match.group(1))

    assert loss <=25, f'FAILED excessive packet loss or No connection: {loss} '
