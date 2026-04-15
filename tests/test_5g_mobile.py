import yaml
import time
import pytest
import re
from jinja2 import Template
from netmiko import ConnectHandler, ReadTimeout


with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def generate_config(template_filename, data):
    with open(template_filename, 'r') as f:
        return Template(f.read()).render(data)


def push_commands(commands):
    """Send one or more config commands to the router."""
    if isinstance(commands, str):
        commands = [commands]
    try:
        net = ConnectHandler(**config['router'])
        output = net.send_config_set(commands, read_timeout=20)
        print(output)
        net.disconnect()
    except ReadTimeout:
        print("Timeout caught — network is restarting.")
    except Exception as e:
        print(f"Connection error: {e}")


def get_status(cmd):
    """Run a show/status command on the router and return output."""
    try:
        net = ConnectHandler(**config['router'])
        result = net.send_command(cmd)
        net.disconnect()
        return result
    except Exception as e:
        return f"Error: {e}"


def wait_for_connection(timeout_seconds, status_cmd, poll_interval=2, message=""):
    if message:
        print(message)

    last_output = ""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        last_output = get_status(status_cmd)
        if "Connected" in last_output:
            print(f"  → Connected early ({int(deadline - time.time())}s remaining)")
            return last_output
        time.sleep(poll_interval)

    print(f"  → Timeout reached after {timeout_seconds}s")
    return last_output  


def assert_connected(status_output):
    match = re.search(r'Status[:\s]+(\S+)', status_output, re.IGNORECASE)
    assert match, f"Could not parse connection status:\n{status_output}"
    state = match.group(1).strip()
    assert state == "Connected", f"Expected Connected, got: {state}"


def assert_ip_received(ifstatus_output):
    line = ifstatus_output.split()[3].strip()
    assert line != '', f"No IP address received: {ifstatus_output}"


def assert_lte_band(expected_band, band_output):
    actual = band_output.split(':')[1].strip()
    assert actual == expected_band, f"Expected band {expected_band}, got: {actual}"


def assert_ping(ping_output):
    """Parse packet loss from ping output regardless of line position or format."""
    print(f"[DEBUG] ping output:\n{ping_output}")  # remove once stable

    match = re.search(r'(\d+)%\s+packet loss', ping_output)
    assert match, f"Could not parse ping output:\n{ping_output}"

    packet_loss = int(match.group(1))
    assert packet_loss <= 25, f"Packet loss {packet_loss}% exceeds 25% threshold"


STATUS_CMD = "vam -a | grep Status && vam -a | grep Slot"

def verify_mobile_interface(sim, timeout=60):
    """Wait for connection, then assert status, IP, and ping."""
    status = wait_for_connection(
        timeout_seconds=timeout,
        status_cmd=STATUS_CMD,
        message=f"  Waiting up to {timeout}s for {sim} to connect..."
    )
    assert_connected(status)
    assert_ip_received(get_status(f"ifstatus | grep {sim}"))
    assert_ping(get_status("ping -I qmimux0 8.8.8.8 -c 4"))


MOBILE_DETAILS = {
    'apn': 'hs.vodafone.ie',
    'username': 'vodafone',
    'password': 'vodafone'
}


def test_auto_mode():
    print("\n=== AUTO MODE ===")

    cmds = generate_config('mobile_uci.j2', MOBILE_DETAILS)
    push_commands(cmds.splitlines())
    time.sleep(15) 

    push_commands(["ifup MOBILE1"])
    status = wait_for_connection(60, "vam -a | grep Status",
                                 message="  Waiting up to 60s for SIM1...")
    assert_connected(status)
    assert_ip_received(get_status("ifstatus | grep MOBILE1"))
    assert_ping(get_status("ping -I qmimux0 8.8.8.8 -c 4"))

    push_commands(["ifup MOBILE2"])
    verify_mobile_interface("MOBILE2", timeout=60)


def test_lte_mode():
    print("\n=== LTE MODE ===")

    for sim in ("MOBILE1", "MOBILE2"):
        print(f"\n  -- {sim} --")
        push_commands([
            f'uci set network.{sim}.service_order="lte"',
            "uci commit network",
            f"ifup {sim}"
        ])
        time.sleep(5)
        verify_mobile_interface(sim, timeout=60)


def test_5g_mode():
    print("\n=== 5G MODE ===")

    for sim in ("MOBILE1", "MOBILE2"):
        print(f"\n  -- {sim} --")
        push_commands([
            f'uci set network.{sim}.service_order="5g"',
            "uci commit network",
            f"ifup {sim}"
        ])
        time.sleep(5)
        verify_mobile_interface(sim, timeout=60)


def test_sim1_lte_bands():
    print("\n=== LTE BAND TEST — SIM1 (Band 3) ===")

    push_commands([
        'uci set network.MOBILE1.service_order="lte"',
        "uci commit network",
        'uci set mobile.main.sim1_lte_bands=3',
        "uci commit mobile",
        "vam restart"
    ])
    time.sleep(5)

    push_commands(["ifup MOBILE1"])
    status = wait_for_connection(60, STATUS_CMD,
                                 message="  Waiting up to 60s for SIM1...")
    assert_connected(status)
    assert_lte_band('3', get_status("vam -a | grep Band"))


def test_sim2_lte_bands():
    print("\n=== LTE BAND TEST — SIM2 (Band 20) ===")

    push_commands([
        'uci set network.MOBILE2.service_order="lte"',
        "uci commit network",
        'uci set mobile.main.sim2_lte_bands=20',
        "uci commit mobile",
        "vam restart"
    ])
    time.sleep(5)

    push_commands(["ifup MOBILE2"])
    status = wait_for_connection(60, STATUS_CMD,
                                 message="  Waiting up to 60s for SIM2...")
    assert_connected(status)
    assert_lte_band('20', get_status("vam -a | grep Band"))


if __name__ == "__main__":
    test_auto_mode()
    test_lte_mode()
    test_5g_mode()
    test_sim1_lte_bands()
    test_sim2_lte_bands()