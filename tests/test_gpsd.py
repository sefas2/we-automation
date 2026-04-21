from net_utils import push_config, run_commands
from jinja2 import Template
import time


with open('templates/gpsd_config.j2', 'r') as f:
    template = Template(f.read()).render()

push_config(template)
time.sleep(30)

def test_gpsd():
    output = run_commands('gpspeek')
    assert 'Fix: 3D' in output, f'Failed: GPS did not connect!'

def test_satellites_connected():
    cmd = run_commands('gpspipe -w -n 20 | grep -o \'"used":true\' | wc -l') 
    assert int(cmd) > 4, 'FAILED: number of active satellities less than 4'
        