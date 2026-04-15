import socket
from netmiko import ConnectHandler
import yaml
from jinja2 import Template
import time
import pytest

with open('config.yaml', 'r') as f:
    inventory = yaml.safe_load(f)

with open('tserv.j2', 'r') as t:
    syslog_template = Template(t.read()).render()

host = inventory['router']['host']
message = b'Serial Port Test'

def load_config():
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            output = net_connect.send_config_set(syslog_template.splitlines())
            print(output)
    except Exception as e:
        print(f'FAILED: {e}')

def load_new_config(cmd):
    try:
        with ConnectHandler(**inventory['router']) as net_connect:
            output = net_connect.send_config_set([cmd])
            print(output)
    except Exception as e:
        print(f'FAILED: {e}')


def socket_established(serial1, serial2):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host, serial1))  # TX
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r.connect((host, serial2))  # RX
    s.sendall(message)
    data = r.recv(1024)
    s.close()
    r.close()
    return data

def test_rs232():
    load_config()
    data = socket_established(1232, 2232)
    assert data == message , f'FAILED:'

def test_rs485():
    load_new_config("uci set tservd.port1.portmode='rs485fdx'")
    load_new_config("uci set tservd.port2.portmode='rs485fdx'")
    load_new_config('uci commit tservd')
    load_new_config('/etc/init.d/tservd restart')
    time.sleep(5)
    data = socket_established(1232, 2232)
    assert data == message , f'FAILED:'
