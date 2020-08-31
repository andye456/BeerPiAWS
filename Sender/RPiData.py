import requests, json
from time import gmtime, strftime
import time

# Temp_File = "/sys/bus/w1/devices/28-021553902fff/w1_slave"
Temp_File = "w1_slave"
host="http://localhost"
port="8081"
send_endpoint="receiver"
receive_endpoint = "get_timeout"

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'
def read_temp_probe():
    with open(Temp_File, "r") as f:
        lines = f.readlines()
    return lines[1].split("=")[1]

def send_data(json_data):
    try:
        r = requests.post(send_url, json=json_data)
        return r.status_code
    except ConnectionRefusedError as e:
        print("connection refused")

# Calls the endpoint to get the timeout value
def get_data():
    r = requests.get(get_url)
    print(r.text)
    try:
        j = json.loads(r.text)
        return j['timeout']
    except TypeError as t:
        return j

while True:
    data = float(read_temp_probe())
    dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data/1000:.2f}'}
    jsonObj = json.dumps(dataObj)
    print(jsonObj)
    # Send data to the AWS server to display on the web page
    send_data(jsonObj)
    # Get the update frequency
    t = get_data()
    time.sleep(int(t))