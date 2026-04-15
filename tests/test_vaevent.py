from netmiko import ConnectHandler, ReadTimeout
import yaml
import socket
import pytest
import re
import requests
import time
from jinja2 import Template

IP = '192.168.100.254'
PORT = 162

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

with open('va_eventd_config.j2', 'r') as v:
    va_template = Template(v.read())
rendered_va_template = va_template.render()

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
    push_config = net_connect.send_config_set(rendered_va_template.splitlines(), read_timeout = 20)
    time.sleep(5)
except Exception as e:
    print({e})
net_connect.disconnect()


def ssh_connection_test(config_name, expect_msg_re, run_commands=[], timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((IP, PORT))
    except PermissionError:
        pytest.fail(f"Permission denied on port {PORT}. Did you run with 'sudo'?")
    try:
        with ConnectHandler(**config[config_name]) as ssh_connect:
            for cmd in run_commands:
                ssh_connect.send_command(cmd)
    except Exception:
        pass
    data, addr = sock.recvfrom(50 * 1024) 
    human_readable_msg = ''.join(chr(byte) for byte in data if 32 <= byte <= 126)
    if 'Router:' in human_readable_msg:
        human_readable_msg = human_readable_msg[human_readable_msg.index('Router:'):]
        human_readable_msg = human_readable_msg[:human_readable_msg.index('0+')]
    sock.close()
    pattern = re.compile(expect_msg_re)
    assert pattern.match(human_readable_msg), f"Unexpected output: {human_readable_msg}"

def web_connection_test(username, password, expect_msg_re, run_commands=[], timeout=30):
    router_ip = config['router']['host'] 
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((IP, PORT))
    except PermissionError:
        pytest.fail(f"Permission denied on port {PORT}. Did you run with 'sudo'?")

    try:
        login_URL = f'http://{router_ip}/cgi-bin/luci'
        
        payload = {
            'username': username, 
            'password': password
        }

        try:
            requests.post(login_URL, data=payload, verify=False, timeout=5)
        except Exception as e:
            print(f"Web request error: {e}")

        start_time = time.time()
        found_message = ""
        
        while (time.time() - start_time) < timeout:
            try:
                sock.settimeout(timeout - (time.time() - start_time))
                data, addr = sock.recvfrom(50 * 1024)
                
                human_readable_msg = ''.join(chr(byte) for byte in data if 32 <= byte <= 126)
                
                if re.search(expect_msg_re, human_readable_msg):
                    found_message = human_readable_msg
                    break
                    
            except socket.timeout:
                break
        
        if not found_message:
            pytest.fail(f"Timeout! Expected pattern '{expect_msg_re}' not found.")

    finally:
        sock.close()

def eth_link_test(config_name, expect_msg_re, run_commands=[], timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((IP, PORT))
    except PermissionError:
        pytest.fail(f"Permission denied on port {PORT}. Did you run with 'sudo'?")

    try:
        try:
            with ConnectHandler(**config[config_name]) as net_connect:
                for cmd in run_commands:
                    print(f"Sending trigger: {cmd}")
                    net_connect.send_command(cmd, expect_string=r".*", read_timeout=5)
        except Exception:
            pass

        start_time = time.time()
        found_message = ""
    
        print(f"Listening for regex: {expect_msg_re}")
        while (time.time() - start_time) < timeout:
            try:
                sock.settimeout(timeout - (time.time() - start_time))
                data, addr = sock.recvfrom(50 * 1024)
                human_readable_msg = ''.join(chr(byte) for byte in data if 32 <= byte <= 126)
                if re.search(expect_msg_re, human_readable_msg):
                    found_message = human_readable_msg
                    break 
            except socket.timeout:
                break
        if not found_message:
            pytest.fail(f"Timeout! Expected pattern '{expect_msg_re}' not found.")
    finally:
        sock.close()


def mobile_link_test(config_name, expect_msg_re, run_commands=[], timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((IP, PORT))
    except PermissionError:
        pytest.fail(f"Permission denied on port {PORT}. Did you run with 'sudo'?")

    try:
        try:
            with ConnectHandler(**config[config_name]) as net_connect:
                for cmd in run_commands:
                    print(f"Sending trigger: {cmd}")
                    net_connect.send_command(cmd, expect_string=r".*", read_timeout=5)
        except Exception:
            pass

        start_time = time.time()
        found_message = ""
    
        print(f"Listening for regex: {expect_msg_re}")
        while (time.time() - start_time) < timeout:
            try:
                sock.settimeout(timeout - (time.time() - start_time))
                data, addr = sock.recvfrom(50 * 1024)
                human_readable_msg = ''.join(chr(byte) for byte in data if 32 <= byte <= 126)
                if re.search(expect_msg_re, human_readable_msg):
                    found_message = human_readable_msg
                    break 
            except socket.timeout:
                break
        if not found_message:
            pytest.fail(f"Timeout! Expected pattern '{expect_msg_re}' not found.")
    finally:
        sock.close()


# --- TEST CASES ---

def test_wrong_password():
    ssh_connection_test("wrong_password", f"Router: .*: SSH login attempt from {IP}: bad password for user root")

def test_correct_password():
    ssh_connection_test("router", f"Router: .*: SSH login: user root from {IP}")

def test_web_correct_password():
    web_connection_test("root", "admin", r"LuCI login: user root") 

def test_web_wrong_password():
    web_connection_test("root", "wrongpass", r"LuCI login attempt: bad password for user root") 

def test_mobile_link_down():
    eth_link_test("router", r"3g link MOBILE1 down", run_commands=['ifdown MOBILE1'])

def test_mobile_link_up():
    eth_link_test("router", r"3g link MOBILE1 up", run_commands=['ifup MOBILE1'])    

def test_eth_link_down():
    eth_link_test("router", r"Ethernet.*down")

def test_eth_link_up():
    eth_link_test("router", r"Ethernet.*up")