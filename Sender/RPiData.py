import logging

import requests, json
from time import gmtime, strftime
import time
import RPi.GPIO as GPIO
from threading import Thread


# Temp_File = "/sys/bus/w1/devices/28-01193c3b3149/w1_slave"
Temp_File = "w1_slave"
host="http://localhost"
host="http://35.176.56.125"
port="8081"
send_endpoint="receiver"
receive_endpoint = "get_interval"

# Temperature limits
desired_temp = 20
margin = 0.5

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'

# Relay pins
RLY1 = 17
RLY2 = 27
RLY3 = 22
RLY4 = 18

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(RLY1, GPIO.OUT)
GPIO.setup(RLY2, GPIO.OUT)
GPIO.setup(RLY3, GPIO.OUT)

logging.basicConfig(level=logging.INFO)

# This is a 'global' - done as a mutable (right way to do it)
relay_state = {'isRelayOn': False}

# Set the relay to on or off
def _set_relay_on(relay: str, state: bool):
    global relay_state
    relay_state['isRelayOn'] = state
    logging.debug("isRelayOn ----- " + str(relay_state['isRelayOn']))
    logging.debug(f'Turning {relay} {state}')
    GPIO.output(relay, state)


# Reads the temperature from the directory where the sensor writes it
# return: the temperature formatted to a float %.2d
def _read_temp_probe():
    try:
        with open(Temp_File, "r") as f:
            lines = f.readlines()
        return int(lines[1].split("=")[1])/1000
    except IndexError as ie:
        logging.warn(ie)


# POSTs the data to the receiver on AWS
def _send_data(json_data):
    try:
        r = requests.post(send_url, json=json_data)
        return r.status_code
    except ConnectionRefusedError as e:
        logging.error("connection refused")

# GETs the interval from the receiver
def _get_data():
    r = requests.get(get_url)
    logging.info(r.text)
    try:
        j = json.loads(r.text)
        return j['timeout']
    except TypeError as t:
        return j

# Reads the temp probe and creates a data object to send to the AWS receiver end point.
# Gets the relay state and reports it back to UI
# Gets the update period from the UI and updates the update period of the UI.
def temperature_control():
    while True:
        data = float(_read_temp_probe())
        # Puts the current temp and timestamp into a JSON object.
        logging.debug("isRelayOn >>>>> "+str(relay_state['isRelayOn']))
        dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data:.2f}', 'isrelayon':relay_state['isRelayOn']}
        jsonObj = json.dumps(dataObj)
        logging.info(jsonObj)
        # Send data to the AWS server to display on the web page
        _send_data(jsonObj)
        # Get the update interval
        t = _get_data()
        time.sleep(int(t))

def control_relay():
    while True:
        logging.debug("state..... "+str(relay_state['isRelayOn']))
        current_temp = _read_temp_probe()
        logging.debug("current_temp = "+str(current_temp))
        if current_temp <= desired_temp - margin:
            _set_relay_on(RLY1, True)
        elif current_temp >= desired_temp + margin:
            _set_relay_on(RLY1, False)
        time.sleep(1)

# GPIO.cleanup()
if __name__ == '__main__':
    Thread(target=temperature_control).start()
    Thread(target=control_relay).start()
