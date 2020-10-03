import logging
import socketio
from datetime import datetime
import subprocess
import requests, json
from time import gmtime, strftime
import time
import RPi.GPIO as GPIO
from threading import Thread
import traceback

logging.basicConfig(level=logging.DEBUG)

# logger = logging.getLogger(__name__)
# logger.setLevel('DEBUG')

sio = socketio.Client()

print("SocketIO Client")
print("---------------")

# Global variables

# Temperature limits
desired_temp = 28
margin = 0.1

# host="http://35.176.56.125:5000"
host = "http://localhost:5000"
update_period = 10
temp_file1 = "w1_slave1"
temp_file2 = "w1_slave2"
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

@sio.event
def connect():
    logging.info('Connection estabished')
    sio.emit("")


# This is called by the SocketServer to set the update period
@sio.on("set_update_period")
def set_update_period(time_seconds):
    # Sets the the read frequency of the temperature probe
    logging.debug(f"Setting the update period to: {time_seconds}")
    global update_period
    update_period = int(time_seconds)

@sio.on("set_required_temp")
def set_required_temp(required_temp):
    logging.debug(f"Setting required temp to: {required_temp}")
    global desired_temp
    desired_temp = int(required_temp)

# Reads the temperatures from the probes
def _read_temp_probe():
    try:
        with open(temp_file1, "r") as f:
            lines = f.readlines()
            t1 = int(lines[1].split("=")[1]) / 1000
        with open(temp_file2, "r") as f:
            lines = f.readlines()
            t2 = int(lines[1].split("=")[1]) / 1000
        return t1, t2
    except IndexError as ie:
        logging.warning(ie)

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

# Turns R1 on and off depending on the desired temp - reads temp every second
def control_temp_relay():
    while True:
        logging.debug(f"control_temp_relay::relay_1_state['isRelayOn'] {str(relay_1_state['isRelayOn'])}")
        current_temp = _read_temp_probe()[0] # This is only for relay 1
        logging.debug(f"control_temp_relay::current_temp = {str(current_temp)}")
        logging.debug("control_temp_relay::dtemp  = "+str(desired_temp))
        if current_temp <= float(desired_temp) - margin:
            _set_relay_on("RLY1", True)
        elif current_temp >= float(desired_temp) + margin:
            _set_relay_on("RLY1", False)
        time.sleep(1)


@sio.event
def dissconnect():
    logging.info('diconnected')


if __name__ == "__main__":
    sio.connect(host)
    # uses the temperature to control the main relay
    # Thread(target=control_temp_relay).start()


