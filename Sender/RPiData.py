import requests, json
from time import gmtime, strftime
import time
import RPi.GPIO as GPIO


Temp_File = "/sys/bus/w1/devices/28-01193c3b3149/w1_slave"
#Temp_File = "w1_slave"
host="http://localhost"
port="8081"
send_endpoint="receiver"
receive_endpoint = "get_interval"

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'

# Relay pins
RLY1 = 17
RLY2 = 27
RLY3 = 22

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(RLY1, GPIO.OUT)
GPIO.setup(RLY2, GPIO.OUT)
GPIO.setup(RLY3, GPIO.OUT)

# Switches on the relay
def set_relay_on(RLY):
    print(f'Turning {RLY} on')
    GPIO.output(RLY, False)

# Switch the relay off
def set_relay_off(RLY):
    print(f'Turning {RLY} off')
    GPIO.output(RLY, True)
    

# Reads the temperature from the directory where the sensor writes it
def read_temp_probe():
    with open(Temp_File, "r") as f:
        lines = f.readlines()
    return lines[1].split("=")[1]

# POSTs the data to the receiver on AWS
def send_data(json_data):
    try:
        r = requests.post(send_url, json=json_data)
        return r.status_code
    except ConnectionRefusedError as e:
        print("connection refused")

# GETs the interval from the receiver
def get_data():
    r = requests.get(get_url)
    print(r.text)
    try:
        j = json.loads(r.text)
        return j['timeout']
    except TypeError as t:
        return j

    '''
while True:
    data = float(read_temp_probe())
    # Puts the current temp and timestamp into a JSON object.
    dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data/1000:.2f}'}
    jsonObj = json.dumps(dataObj)
    print(jsonObj)
    # Send data to the AWS server to display on the web page
    send_data(jsonObj)
    # Get the update interval
    t = get_data()
    time.sleep(int(t))
    '''
i=0
while i < 5:
    set_relay_on(RLY1)
    set_relay_on(RLY2)
    set_relay_on(RLY3)
    time.sleep(1)
    set_relay_off(RLY1)
    set_relay_off(RLY2)
    set_relay_off(RLY3)
    time.sleep(1)
    i+=1
GPIO.cleanup()
