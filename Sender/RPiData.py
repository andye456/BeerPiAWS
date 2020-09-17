import logging

import requests, json
from time import gmtime, strftime
import time
import RPi.GPIO as GPIO
from threading import Thread
import traceback


Temp_File = "w1_slave"
host="http://localhost"
port="8081"
send_endpoint="receiver"
receive_endpoint = "get_interval"
temp_endpoint = "get_temp"

# Temperature limits
desired_temp = 28
margin = 0.1

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'
get_temp =  f'{host}:{port}/{temp_endpoint}'

# Relay pins
RLY1 = 17
RLY2 = 27
RLY3 = 22
RLY4 = 18

GPIO.cleanup()
GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(RLY1, GPIO.OUT)
GPIO.setup(RLY2, GPIO.OUT)
GPIO.setup(RLY3, GPIO.OUT)
GPIO.setup(RLY4, GPIO.OUT)

logging.basicConfig(level=logging.DEBUG)

# This is a 'global' - done as a mutable (right way to do it)
relay_state = {'isRelayOn': False}

# Set the relay to on or off
def _set_relay_on(relay: str, state: bool):
    global relay_state
    relay_state['isRelayOn'] = state
    logging.debug("isRelayOn ----- " + str(relay_state['isRelayOn']))
    logging.debug(f'Turning {relay} {state}')
    # Seems a bit weird that passing false to the output sends it high - so invert it
    state = not state
    GPIO.output(relay, state)


# Reads the temperature from the directory where the sensor writes it
# return: the temperature formatted to a float %.2d
def _read_temp_probe():
    try:
        with open(Temp_File, "r") as f:
            lines = f.readlines()
        return int(lines[1].split("=")[1])/1000
    except IndexError as ie:
        logging.warning(ie)


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

def _get_required_temp():
    r = requests.get(get_temp)
    logging.info("required_temp returned from endpoint = "+r.text)
    try:
        j = json.loads(r.text)
        return j['temp']
    except TypeError as t:
        return j
    except Exception as e:
        logging.debug("_get_required_temp error!!! "+str(e))
        logging.debug(traceback.format_exc())
        return desired_temp


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
        # global desired_temp
        dtemp = _get_required_temp()
        logging.debug("control_relay::dtemp  = "+str(dtemp))
        if current_temp <= float(dtemp) - margin:
            _set_relay_on(RLY2, True)
        elif current_temp >= float(dtemp) + margin:
            _set_relay_on(RLY2, False)
        time.sleep(1)

if __name__ == '__main__':
    Thread(target=temperature_control).start()
    Thread(target=control_relay).start()
