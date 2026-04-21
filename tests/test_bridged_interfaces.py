from net_utils import push_config, run_commands
from jinja2 import Template
import time

with open('templates/bridged_interface_template.j2', 'r') as v:
    template = (Template(v.read()).render()).splitlines()

push_config(template)

def test_ip_received():
    output = run_commands('ifstatus | grep lan0')
    ip_address = output.split()[3].strip()
    assert ip_address == '192.168.100.1/24'

def test_ping_connectivity_portA():
    output = run_commands('ping 192.168.100.254 -c 5')
    assert '0% packet loss' in output
    print(output)
    print('\n=======Switch to PORTB===========')
    time.sleep(8)

def test_ping_connectivity_portB():
    output = run_commands('ping 192.168.100.254 -c 5')
    assert '0% packet loss' in output
    print(output)
    print('\n=======Switch to PORTC===========')
    
    time.sleep(8)

def test_ping_connectivity_portC():
    output = run_commands('ping 192.168.100.254 -c 5')
    assert '0% packet loss' in output
    print(output)
    print('\n=======Switch to PORTD===========')
    time.sleep(8)

def test_ping_connectivity_portD():
    output = run_commands('ping 192.168.100.254 -c 5')
    assert '0% packet loss' in output
    print(output)
