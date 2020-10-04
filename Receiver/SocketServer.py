import logging, json
from flask import Flask, render_template
from flask_socketio import SocketIO
import glob
import os

########
# This is The Socket IO server that the clients (RPi and web page) are going to connect to.
# Requests will be sent back to the RPi once a socket to this server has been created by the RPi
########

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', ping_interval=300, ping_timeout=300)

req_temp = 25
req_update_period = 10
relay_state= {"1": {"state": False}, "2": {"state": False}, "3": {"state": False}, "4": {"state": False}}

@socketio.on('connect')
def connect():
    logging.debug("Connected...")
    # Called when the web page connects
    socketio.emit("update_req_period", req_update_period) # This is to update the web page
    socketio.emit("set_required_temp", req_temp) # this is to update the web page
    logging.debug("Sending Relay state....")
    # This is a bit back-to-front, it 'calls' a function in the client to then 'emit' the relay states to here
    socketio.emit("get_relay_state") # this emits to update_relay_state as RLY1set is controlled by the RPi

# This is called from the html and sends the value on to the RPi
@socketio.on("set_update_period")
def set_update_period(time_seconds):
    logging.debug("set_update_period " + str(time_seconds))
    global req_update_period
    req_update_period = int(time_seconds)
    socketio.emit("set_update_period", time_seconds)

# This is called from the html and sends the value on to the RPi
@socketio.on("set_required_temp")
def set_required_temp(required_temp):
    logging.debug("set_required_temp " + str(required_temp))
    global req_temp
    req_temp = int(required_temp)
    socketio.emit("set_required_temp", required_temp)

# called by the client to set the temps to display in the UI
@socketio.on("set_temp_from_probes")
def set_temp_from_probes(temps):
    logging.debug(f"temps : {temps}")
    socketio.emit('update_temps',temps)

# This is called by the RPi and changes the state of the relay that is controlled by the RPi (heater)
@socketio.on('update_relay_state')
def update_relay_state(relay_state):
    logging.debug(f"relay_state: {relay_state}")
    socketio.emit('update_relay_state',relay_state)

# This is called by the UI and set the state of the other relays
@socketio.on('set_relay_state')
def set_relay_state(relay_state):
    socketio.emit("set_relay_state", relay_state)

@socketio.on("camera")
def camera(cmd):
    socketio.emit("camera",cmd)

@socketio.on('get_latest_snap')
def get_latest_snap():
    list_of_files = glob.glob('/home/bitnami/htdocs/static/*.jpg')
    # list_of_files = glob.glob('C:/Users/andye/Documents/static/*.jpg')
    latest_file = max(list_of_files, key=os.path.getctime)
    logging.debug(f'get_latest_snap: {latest_file}')
    socketio.emit('set_latest_snap',latest_file)

@socketio.on('get_latest_vid')
def get_latest_vid():
    list_of_files = glob.glob('/home/bitnami/htdocs/static/*.mp4')
    # list_of_files = glob.glob('C:/Users/andye/Documents/static/*.mp4')
    latest_file = max(list_of_files, key=os.path.getctime)
    logging.debug(f'get_latest_vid: {latest_file}')
    socketio.emit('set_latest_vid',latest_file)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
