from netmiko import ConnectHandler, ReadTimeout
from jinja2 import Template
import yaml
import time
from datetime import datetime, timezone
import pytest


with open('config.yaml', 'r') as f:
    login = yaml.safe_load(f) 

with open('ntp_config.j2', 'r') as t:
    template = Template(t.read())
rendered = template.render()

try:
    net_connect = ConnectHandler(**login['router'])
    push_config = net_connect.send_config_set(rendered.splitlines(), read_timeout = 20)
    time.sleep(10)
except ReadTimeout:
    print('====== Router is being rebooted =======')
except Exception as e:
    print({e})
net_connect.disconnect()

while True:
    try:
        net_connect = ConnectHandler(**login['router'])
        print('Router is back online')
        break
    except Exception:
        time.sleep(10)

output = net_connect.send_command('date')
net_connect.disconnect()

def test_ntp_client_web():
    pass

def test_utc():
    router_time = datetime.strptime(
        " ".join(output.split()[0:6]),
        "%a %b %d %H:%M:%S %Z %Y"
    ).replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)

    delta = abs((now_utc - router_time).total_seconds())
    assert delta < 60