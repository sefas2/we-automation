import socket
from netmiko import ConnectHandler
import re
import pytest
from jinja2 import Template
import yaml
import requests
import time

host = '192.168.100.254'
port = 514

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

with open('syslog_config.j2', 'r') as v:
    syslog_template = Template(v.read())
rendered_syslog_template = syslog_template.render()

with open('snmpd_config.j2', 'r') as s:
    snmp_template = Template(s.read())
rendered_snmp_template = snmp_template.render()

try:
    net_connect = ConnectHandler(**config['router'])
    push_config = net_connect.send_config_set(rendered_snmp_template.splitlines(), read_timeout = 20)
    time.sleep(5)
except Exception as e:
    print({e})
net_connect.disconnect()

try:
    net_connect = ConnectHandler(**config['router'])
    push_config = net_connect.send_config_set(rendered_syslog_template.splitlines(), read_timeout = 20)
    time.sleep(5)
except Exception as e:
    print({e})
net_connect.disconnect()

def connection_test(config_name):
        try:
            with ConnectHandler(**config[config_name]) as connection:
                pass
        except Exception as e:
               print(e)   

def web_connection(config_name):
        router_ip = config[config_name]['host'] 
        login_URL = f'http://{router_ip}/cgi-bin/luci'
        payload = {
                'username': config[config_name]['username'], 
                'password': config[config_name]['password']
        }
        try:
            requests.post(login_URL, data=payload, timeout=5)
        except Exception as e:
            print(f"Web request error: {e}")

def test_ssh_login():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((host, port))
                connection_test('router')
                s.settimeout(5)
                conn, addr = s.recvfrom(1024)
                text = conn.decode(errors='ignore')
        assert re.search(r'Successful SSH Access for User root', text)

def test_wrong_ssh_login():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((host, port))
                connection_test('wrong_password')
                s.settimeout(5)
                conn, addr = s.recvfrom(1024)
                text = conn.decode(errors='ignore')
        assert re.search(r'Wrong SSH Password Attempt for User root', text)

def test_web_login():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((host, port))
                web_connection('router')
                s.settimeout(5)
                conn, addr = s.recvfrom(1024)
                text = conn.decode(errors='ignore')
        assert re.search(r'Successful Web Access for User root', text)

def test_web_incorrect_login():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((host, port))
                web_connection('wrong_password')
                s.settimeout(5)
                conn, addr = s.recvfrom(1024)
                text = conn.decode(errors='ignore')
        assert re.search(r'Wrong Web Password for User root', text)