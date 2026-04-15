Automated testing and configuration framework for Westermo routers running OpenWRT/LuCI.
Built with Python, Netmiko, pytest, and Jinja2.
This suite was developed to automate real-world validation tasks including mobile connectivity,
SNMP, NTP, syslog, serial ports, VLAN, Mobile connection testing for 5g/4g/2g and critical process resilience testing.

Project Structure

we-automation/
├── README.md
├── .gitignore
├── config.example.yaml       ← copy to config.yaml and fill in your credentials
├── requirements.txt
├── templates/
│   ├── snmpd_config.j2
│   ├── syslog_config.j2
│   ├── ntp_config.j2
│   ├── va_eventd_config.j2
│   ├── tserv.j2
│   ├── mobile_uci.j2
│   ├── multiwan.j2
│   └── vlan_config.j2
└── tests/
    ├── test_snmp.py
    ├── test_syslog.py
    ├── test_ntp.py
    ├── test_ntp_web.py
    ├── test_mobile.py
    ├── test_5g_mobile.py
    ├── test_multiwan.py
    ├── test_vaevent.py
    ├── test_tservd.py
    ├── test_vlan100.py
    └── test_crit_process.py

Test Coverage:
test_snmp.py -> SNMPv1, SNMPv2c, SNMPv3 (SHA/MD5), OID access control
test_syslog.py -> SSH and web login events forwarded to syslog server
test_ntp.py -> NTP sync accuracy asserts router time within 60s of UTC
test_ntp_web.py -> Timezone configuration via LuCI web UI using Selenium
test_mobile.py -> 4G mobile interface auto/LTE/GPRS modes, SIM1/SIM2, LTE band selection
test_5g_mobile.py -> 5G mobile interface same coverage extended to 5G mode
test_multiwan.py -> Dual-SIM failover preempt enabled/disabled, SIM priority switching
test_vaevent.py -> VA event daemon SSH/web login traps, Ethernet/mobile link events
test_tservd.py -> Serial port server. RS232 and RS485 full-duplex modes over TCP
test_vlan100.py -> VLAN 100 interface creation, link state, and ping connectivity
test_crit_process.py -> Critical process watchdog. Kills and verifies auto recovery


Netmiko : SSH connection and command execution on router
pytest: Test framework and assertion engine
jinja2: Configuration templating
requests: HTTP/web interface testing
Selenium: Browser automation for LuCI web UI
PyYAML: Inventory and config file parsing
socket: UDP listener for SNMP traps and syslog
subprocess: Local snmpwalk execution

Notes:
config.yaml is excluded from version control. Use config.example.yaml as a template
Test that listen on privileged ports (162, 514) require sudo
test_multiwan.py uses a 120-second polling timeout for interface state changes. This is intentional
test_crit_process.py kills critical router processes.
The NTP template (templates/ntp_config.j2) contains an NTP server IP. Replace it with your own NTP server address before running.

Running Test
Single test = pytest tests/test_snmp.py -v
All tests = pytest tests/ -v

Requirements

Python 3.9+
Westermo router running OpenWRT/LuCI
snmpwalk installed on the test machine (sudo apt install snmp)
ChromeDriver installed for test_ntp_web.py (Selenium)
Physical serial loopback cable for test_tservd.py