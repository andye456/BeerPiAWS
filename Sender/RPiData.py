import requests, json
from time import gmtime, strftime

# Temp_File = "/sys/bus/w1/devices/28-021553902fff/w1_slave"
Temp_File = "w1_slave"

def read_temp_probe():
    with open(Temp_File, "r") as f:
        lines = f.readlines()
    return lines[1].split("=")[1]

def send_data(json_data):
    try:
        r = requests.post("http://localhost:8080/receiver", json=json_data)
        return r.status_code
    except ConnectionRefusedError as e:
        print("connection refused")

data = float(read_temp_probe())
dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data/1000:.2f}'}
jsonObj = json.dumps(dataObj)
print(jsonObj)
send_data(jsonObj)