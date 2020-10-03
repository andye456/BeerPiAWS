import logging
from flask import Flask, render_template
from flask_socketio import SocketIO

########
# This is The Socket IO server that the clients (RPi and web page) are going to connect to.
# Requests will be sent back to the RPi once a socket to this server has been created by the RPi
########

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', ping_interval=300, ping_timeout=300)

req_temp = 25
req_update_period = 10

@socketio.on('connect')
def connect():
    logging.debug("Connected...")
    socketio.emit("update_req_period", req_update_period) # This is to update the web page
    socketio.emit("update_req_temp", req_temp) # this is to update the web page

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

# This reads the current value for the update period and sets the val in the UI
def get_update_period():
    pass

# Read the current value for the required temp and updates the UI
def get_required_temp():
    pass

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
