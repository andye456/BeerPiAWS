import logging, json
from flask import Flask, render_template
from flask_socketio import SocketIO
import glob
import os
from datetime import datetime
########
# This is The Socket IO server that the clients (RPi and web page) are going to connect to.
# Requests will be sent back to the RPi once a socket to this server has been created by the RPi
########

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', ping_interval=300, ping_timeout=300)

req_temp = 25
req_update_period = 1
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

# Gets the temperature from the PRi probes
@socketio.on("get_temp_from_pi")
def get_temp_from_pi():
        socketio.emit("get_temp")

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
    # write the temperature to a csv file.
    today = datetime.now()
    date_string = today.strftime("%d-%m-%Y_%H-%M-%S")
    file_date = today.strftime("%d-%m-%Y")
    csv_file = f"temp_files/temp_data_{file_date}.csv"
    with open(csv_file,'a') as f:
        logging.debug(f'Logging to file {csv_file}')
        if os.stat(csv_file).st_size == 0:
            f.writelines('time,temp1,temp2,relay1\n')
        if relay_state['1']['state']:
            f.writelines(f"{date_string},{temps['t1']},{temps['t2']},1\n")
        elif not relay_state['1']['state']:
            f.writelines(f"{date_string},{temps['t1']},{temps['t2']},0\n")

    socketio.emit('update_temps',temps)

# This is called by the RPi and changes the state of the relay that is controlled by the RPi (heater)
@socketio.on('update_relay_state')
def update_relay_state(r_state):
    logging.debug(f"relay_state: {r_state}")
    global relay_state
    relay_state = r_state
    socketio.emit('update_relay_state',r_state)

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
    latest_file = os.path.basename(max(list_of_files, key=os.path.getctime))
    logging.debug(f'get_latest_snap: {latest_file}')
    socketio.emit('set_latest_snap','static/'+latest_file)

@socketio.on('get_latest_vid')
def get_latest_vid():
    list_of_files = glob.glob('/home/bitnami/htdocs/static/*.mp4')
    # list_of_files = glob.glob('C:/Users/andye/Documents/static/*.mp4')
    latest_file = os.path.basename(max(list_of_files, key=os.path.getctime))
    logging.debug(f'get_latest_vid: static/{latest_file}')
    socketio.emit('set_latest_vid','static/'+latest_file)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
