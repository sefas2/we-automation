from netmiko import ConnectHandler, ReadTimeout
import yaml
import time


with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
"""
def push_config(uci_set_list):
    try:
        net_connect = ConnectHandler(**config['router'])
        output = net_connect.send_config_set(uci_set_list, read_timeout=20)
        print(output)
    except ReadTimeout:
        print('Service is being restarted...')
    except Exception as e :
        print(e)
"""

def run_command(conn, command):
    try:
        output = conn.send_command(command)
        return output
    except Exception as e :
        print(e)
    return ''

net_connect = ConnectHandler(**config['router'])
processes = {
            'uhttpd' : '',
            'multiwan' : '',
            'dnsmasq' : '',
            'syslogd' : '',
            'va_eventd' : '',
            'va_mobile' : '',
            'snmpd' : '',
            'cwatch' : ''
          #  'dropbear' : ''
            }

for k, v in processes.items():
    command_output = run_command(net_connect, f'pgrep -f {k}')
    processes[k] = command_output
    print(f'Process {k} found (pid = {command_output})')

for values in processes.values():
    kill_process = run_command(net_connect, f'kill -9 {values}')
    
print('Killed all processes')
print('Waiting for the processes to come up...')
print('--------------')
time.sleep(45)
for k, v in processes.items():
    command_output = run_command(net_connect, f'pgrep -f {k}')
    process_status = 'WORKING'
    if len(command_output) == 0:
        process_status = 'ERROR'
    print(f'Process {k:<12} was {v:<6} now {command_output:<6} ======> {process_status}')
    #processes[k] = command_output
#print(processes)

net_connect.disconnect()