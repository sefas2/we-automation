from netmiko import ConnectHandler
import yaml
import pytest
import time
from jinja2 import Template
import re

MOBILE_DETAILS = {
    'apn': 'hs.vodafone.ie',
    'username': 'vodafone',
    'password': 'vodafone'
}

Interface_timeout = 120
POLL_INTERVAL = 10 

with open('config.yaml', 'r') as f:
    inventory = yaml.safe_load(f)

with open('templates/mobile_uci.j2', 'r') as t:
    template_mobile = (Template(t.read()).render(MOBILE_DETAILS)).splitlines()

with open('templates/multiwan.j2', 'r') as m:
    template_multiwan = (Template(m.read()).render()).splitlines()

configs = template_mobile + template_multiwan


def load_config():
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            net_connect.send_config_set(configs, cmd_verify=False)
    except Exception as e:
        pytest.fail(f'Config load failed: {e}')


def run_command(cmd):
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            output = net_connect.send_command(cmd, read_timeout=60)
            return output
    except Exception as e:
        pytest.fail(f'Command "{cmd}" failed: {e}')


def get_statuses():
    output = run_command("mwan_status")
    pattern = r'^(MOBILE\d+)\s+is\s+(up|down)'
    matches = re.findall(pattern, output, re.MULTILINE)

    if not matches:
        pytest.fail(f"Could not parse multiwan output:\n{output}")

    return {iface: state for iface, state in matches}

# TESTS

def test_preempt_multiwan_sim1_up_sim2_down():
    print('\n=== sim1 up, sim2 down — preempt enabled ===')
    load_config()
    time.sleep(120)
    statuses = get_statuses()
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_preempt_multiwan_sim1_down_sim2_up():
    print('\n=== sim1 down, sim2 up — preempt enabled ===')
    run_command('ifdown MOBILE1')  
    time.sleep(120) 
    statuses = get_statuses()
    assert statuses['MOBILE1'] == 'down'
    assert statuses['MOBILE2'] == 'up'


def test_preempt_multiwan_sim1():
    print('\n=== multiwan reverts to sim1 (higher priority, preempt) ===')
    time.sleep(140)
    statuses = get_statuses()
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_multiwan_sim1_up_sim2_down():
    print('\n=== sim1 up, sim2 down — no preempt ===')
    run_command('uci set multiwan.config.preempt=no')
    run_command('uci commit multiwan')
    run_command('/etc/init.d/multiwan restart')
    time.sleep(140)
    statuses = get_statuses()
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_multiwan_sim1_down_sim2_up():
    print('\n=== sim1 down, sim2 up — no preempt ===')
    run_command('ifdown MOBILE1')   
    time.sleep(140)
    statuses = get_statuses()
    assert statuses['MOBILE1'] == 'down'
    assert statuses['MOBILE2'] == 'up'