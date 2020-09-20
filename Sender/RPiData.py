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
relay_endpoint = 'get_relay'

# Temperature limits
desired_temp = 28
margin = 0.1

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'
get_temp =  f'{host}:{port}/{temp_endpoint}'
get_relay_url = f'{host}:{port}/{relay_endpoint}'

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

logging.basicConfig(level=logging.INFO)

# This is a 'global' - done as a mutable (right way to do it)
relay_1_state = {'isRelayOn': False}
relay_2_state = {'isRelayOn': False}
relay_3_state = {'isRelayOn': False}
relay_4_state = {'isRelayOn': False}

# Set the relay to on or off
def _set_relay_on(relay: str, state: bool):
    # These variables maintain state to send to server
    global relay_1_state
    global relay_2_state
    global relay_3_state
    global relay_4_state
    if relay == "RLY1":
        relay_1_state['isRelayOn'] = state
    if relay == "RLY2":
        relay_2_state['isRelayOn'] = state
    if relay == "RLY3":
        relay_3_state['isRelayOn'] = state
    if relay == "RLY4":
        relay_4_state['isRelayOn'] = state

    logging.debug("_set_relay_on::relay_1_state['isRelayOn']----- " + str(relay_1_state['isRelayOn']))
    logging.debug(f'Turning {relay} {state}')
    # Seems a bit weird that passing false to the output sends it high - so invert it
    state = not state
    # relay here needs to be the number not the name of the relay
    GPIO.output(eval(relay), state)


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

# This polls the relay_state end point and gets the json that contains the state of the relays that are set from the check boxes
def get_relay_state():
    while True:
        # Get the current relay instruction from the end point
        for i in range(2,5):
            logging.debug("GET: "+get_relay_url+"/"+str(i))
            state = requests.get(get_relay_url+"/"+str(i))
            j = json.loads(state.text)
            _set_relay_on("RLY"+str(i), j[str(i)]['state'])
        time.sleep(1)

# def get_current_relay_states():
#     global relay_2_stat
#     global relay_3_state
#     global relay_4_state
#     return relay_2_state, relay_3_state, relay_4_state

# Reads the temp probe and creates a data object to send to the AWS receiver end point.
# Gets the relay state and reports it back to UI
# Gets the update period from the UI and updates the update period of the UI.
def temperature_control():
    while True:
        data = float(_read_temp_probe())
        # Puts the current temp and timestamp into a JSON object.
        logging.debug("isRelayOn >>>>> " + str(relay_1_state['isRelayOn']))
        dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data:.2f}', 'isrelayon':relay_1_state['isRelayOn']}
        jsonObj = json.dumps(dataObj)
        logging.info(jsonObj)
        # Send data to the AWS server to display on the web page
        _send_data(jsonObj)
        # Get the update interval
        t = _get_data()
        time.sleep(int(t))

def control_temp_relay():
    while True:
        logging.debug(f"control_temp_relay::relay_1_state['isRelayOn'] {str(relay_1_state['isRelayOn'])}")
        current_temp = _read_temp_probe() # This is only for relay 1
        logging.debug(f"control_temp_relay::current_temp = {str(current_temp)}")
        # global desired_temp
        dtemp = _get_required_temp()
        logging.debug("control_temp_relay::dtemp  = "+str(dtemp))
        if current_temp <= float(dtemp) - margin:
            _set_relay_on("RLY1", True)
        elif current_temp >= float(dtemp) + margin:
            _set_relay_on("RLY1", False)
        time.sleep(1)


if __name__ == '__main__':
    # gets the temperature from the temp probe in a thread
    Thread(target=temperature_control).start()
    # uses the temperature to control the main relay
    Thread(target=control_temp_relay).start()
    # reads the state of the check boxes and sets the other relays accordingly
    Thread(target=get_relay_state).start()