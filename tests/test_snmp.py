import yaml
import subprocess
from jinja2 import Template
from netmiko import ConnectHandler


# Load router config
with open('config.yaml', 'r') as f:
    inventory = yaml.safe_load(f)

# Load SNMP template
with open('snmpd_config.j2', 'r') as s:
    template = Template(s.read()).render()


def config_router():
    """Push SNMP config to router."""
    try:
        net = ConnectHandler(**inventory['router'])
        output = net.send_config_set(template.splitlines())
        print(output)
        net.disconnect()
    except Exception as e:
        print(f"Failed: {e}")


def run_snmpwalk(cmd):
    """Run snmpwalk locally on the PC."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        return result.stdout
    except Exception as e:
        return f"Failed: {e}"


def test_snmpv1():
    output = run_snmpwalk("snmpwalk -v1 -c public 192.168.100.1")
    assert len(output.splitlines()) > 10, "FAILED: SNMPv1 output too short"
    print("SNMPv1 OK")


def test_snmpv2():
    output = run_snmpwalk("snmpwalk -v2c -c public 192.168.100.1")
    assert len(output.splitlines()) > 10, "FAILED: SNMPv2 output too short"
    print("SNMPv2 OK")

def test_snmpv3_SHA():
    output = run_snmpwalk("snmpwalk -v3 -l authPriv -u user2 -a SHA -A virtual1 -x DES -X virtual1 192.168.100.1 .1.3.6.1.2.1.1")
    assert len(output.splitlines()) > 10, "FAILED: SNMPv3 output too short"
    print("SNMPv3 OK")

def test_snmpv3_MD5():
    output = run_snmpwalk("snmpwalk -v3 -l authPriv -u user3 -a MD5 -A virtual1 -x AES -X virtual1 192.168.100.1 .1.3.6.1.2.1.2")
    assert len(output.splitlines()) > 10, "FAILED: SNMPv3 output too short"
    print("SNMPv3 OK")

def test_user_access():
    output = run_snmpwalk("snmpwalk -v3 -l authPriv -u user3 -a MD5 -A virtual1 -x AES -X virtual1 192.168.100.1 .1.4")
    assert 'No more variables left in this MIB View' in output.splitlines()[0], "FAILED: User can access to different OIDs"

if __name__ == "__main__":
    config_router()
    test_snmpv1()
    test_snmpv2()
    test_snmpv3_SHA()
    test_snmpv3_MD5()
    test_user_access()