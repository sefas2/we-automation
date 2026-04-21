from net_utils import push_config, run_commands
from jinja2 import Template
import re
import time

with open('templates/adsl_vdsl_pppoe_config.j2', 'r') as v:
    template = (Template(v.read()).render()).splitlines()

push_config(template)
time.sleep(30)

def check_vdsl_up():
    output = run_commands('dsl')
    pattern = r'Line State:\s*UP'
    match = re.search(pattern, output)
    return match

def check_ip_received():
    output = run_commands('ifstatus PPPoE')
    match = re.search(r'(10\.100\.226\.\d+)', output)
    return match.group(1) if match else None

def check_data_rate():
    output = run_commands('dsl | grep Data')
    speed = {'dl' : float(output.split()[2].strip()), 'ul' : float(output.split()[5].strip())}
    if speed['dl'] > 25 and speed['ul'] > 1.8:
        return speed    

def test_vdsl_up():
    assert check_vdsl_up(), f'FAILED VDSL Status is DOWN'

def test_ip_received():
    assert check_ip_received(), f'Did not received IP'

def test_check_data_rate():
    assert check_data_rate(), f'Data rate speed is less than 70Mbs'