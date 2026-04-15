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

with open('mobile_uci.j2', 'r') as t:
    template_mobile = (Template(t.read()).render(MOBILE_DETAILS)).splitlines()

with open('multiwan.j2', 'r') as m:
    template_multiwan = (Template(m.read()).render()).splitlines()

configs = template_mobile + template_multiwan


def load_config():
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            net_connect.send_config_set(configs, cmd_verify=False)
    except Exception as e:
        pytest.fail(f'Config load failed: {e}')


def run_command(cmd, timing=False):
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            if timing:
                output = net_connect.send_command_timing(cmd, read_timeout=30)
            else:
                output = net_connect.send_command(cmd, read_timeout=60)
            return output
    except Exception as e:
        pytest.fail(f'Command "{cmd}" failed: {e}')


def assert_multiwan(output):
    pattern = r'^(MOBILE\d+)\s+is\s+(up|down)'
    matches = re.findall(pattern, output, re.MULTILINE)
    assert matches, f'Pattern not found in output:\n{output}'
    return {iface: status for iface, status in matches}


def wait_for_status(expected: dict, timeout=Interface_timeout, interval=POLL_INTERVAL):
    deadline = time.time() + timeout
    last_statuses = {}
    while time.time() < deadline:
        output = run_command('mwan_status')
        last_statuses = assert_multiwan(output)
        if all(last_statuses.get(k) == v for k, v in expected.items()):
            return last_statuses
        time.sleep(interval)
    pytest.fail(
        f'Timeout waiting for {expected}. Last seen: {last_statuses}'
    )

# TESTS

def test_preempt_multiwan_sim1_up_sim2_down():
    print('\n=== sim1 up, sim2 down — preempt enabled ===')
    load_config()
    statuses = wait_for_status({'MOBILE1': 'up', 'MOBILE2': 'down'})
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_preempt_multiwan_sim1_down_sim2_up():
    print('\n=== sim1 down, sim2 up — preempt enabled ===')
    run_command('ifdown MOBILE1', timing=True)   
    statuses = wait_for_status({'MOBILE1': 'down', 'MOBILE2': 'up'})
    assert statuses['MOBILE1'] == 'down'
    assert statuses['MOBILE2'] == 'up'


def test_preempt_multiwan_sim1():
    print('\n=== multiwan reverts to sim1 (higher priority, preempt) ===')
    statuses = wait_for_status(
        {'MOBILE1': 'up', 'MOBILE2': 'down'},
        timeout=Interface_timeout + 30
    )
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_multiwan_sim1_up_sim2_down():
    print('\n=== sim1 up, sim2 down — no preempt ===')
    run_command('uci set multiwan.config.preempt=no', timing=True)
    run_command('uci commit multiwan', timing=True)
    run_command('/etc/init.d/multiwan restart', timing=True)
    statuses = wait_for_status(
        {'MOBILE1': 'up', 'MOBILE2': 'down'},
        timeout=Interface_timeout + 30
    )
    assert statuses['MOBILE1'] == 'up'
    assert statuses['MOBILE2'] == 'down'


def test_multiwan_sim1_down_sim2_up():
    print('\n=== sim1 down, sim2 up — no preempt ===')
    run_command('ifdown MOBILE1', timing=True)   # <-- timing mode again
    statuses = wait_for_status({'MOBILE1': 'down', 'MOBILE2': 'up'})
    assert statuses['MOBILE1'] == 'down'
    assert statuses['MOBILE2'] == 'up'