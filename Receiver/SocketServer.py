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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', ping_interval=300, ping_timeout=300)

# List position of the photo list
current_pos = 0

# Write the temp and time period to a file.
def _write_save_data(temp, period, last_update):
    with open("save_data.txt", "w") as f:
        f.write(f'{temp} {period} {last_update}')

# Opens the file containing the last used values
def _read_save_data():
    try:
        with open("save_data.txt", "r") as f:
            for line in f:
                d = line.split()
                return d[0], d[1], d[2]
    except FileNotFoundError as f:
        # if file does not exist then use vals 20 deg and 300 seconds (5 mins) and some arbitrary time
        return 20,300,"1970-01-01 00:00:00"

req_temp,req_update_period, last_time_updated = _read_save_data()
relay_state= {"1": {"state": False}, "2": {"state": False}, "3": {"state": False}, "4": {"state": False}}


@socketio.on('connect')
def connect():
    logging.debug("Connected...")
    # Called when the web page connects
    socketio.emit("update_req_period", req_update_period) # This is to update the web page and the val stored in Rpi
    socketio.emit("set_required_temp", req_temp) # this is to update the web page and val stored in RPi
    socketio.emit("set_UI_last_updated",last_time_updated)
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
    global req_update_period, req_temp, last_time_updated
    req_update_period = int(time_seconds)
    socketio.emit("set_update_period", time_seconds)
    _write_save_data(req_temp, req_update_period,last_time_updated)

# This is called from the html and sends the value on to the RPi
@socketio.on("set_required_temp")
def set_required_temp(required_temp):
    logging.debug("set_required_temp " + str(required_temp))
    global req_temp, req_update_period
    req_temp = int(required_temp)
    socketio.emit("set_required_temp", required_temp)
    _write_save_data(req_temp, req_update_period)

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
    # Updates the temps in the UI
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

# This is an endpoint so that a query string can be used to set the relay state the values expected.
# To set the relay state then pass a json string like this - this is derived from the checkbox on the web page
# {'1': {'state': False, 'timeout': ''}, '2': {'state': True, 'timeout': ''}, '3': {'state': False, 'timeout': ''}, '4': {'state': False, 'timeout': ''}}
# /set_relay_state/1.False.0~2.True.0~3.False.0~4.False.0
@app.route('/set_relay_state/<numstate>', methods=['GET'])
def relay_state(numstate):
    logging.debug('Setting relays via url')
    r1 = numstate.split('~')[0]
    r2 = numstate.split('~')[1]
    r3 = numstate.split('~')[2]
    r4 = numstate.split('~')[3]
    all_states = {
        r1.split('.')[0]:{'state':r1.split('.')[1], 'timeout':r1.split('.')[2]},
        r2.split('.')[0]:{'state':r2.split('.')[1], 'timeout':r2.split('.')[2]},
        r3.split('.')[0]:{'state':r3.split('.')[1], 'timeout':r3.split('.')[2]},
        r4.split('.')[0]:{'state':r4.split('.')[1], 'timeout':r4.split('.')[2]}
                  }
    set_relay_state(all_states)
    return ""

# @app.route('/')
# def home():
#     return '<h1><a href="/beer">Goto RPi Beer</h1>'

@app.route('/beer')
def beer_home():
    return render_template("beer.html", number=1)

@socketio.on("camera")
def camera(cmd):
    socketio.emit("camera",cmd)

# Get the snap that is current (0) or before it etc. -1, 0, +1
# current_pos is the position relative to the end of the list, 0 is end -1 is one back etc.
@socketio.on('get_latest_snap')
def get_latest_snap(pos):
    global current_pos
    current_pos = current_pos+pos
    if pos == 0:
        current_pos = 0
    list_of_files = glob.glob('/home/bitnami/htdocs/static/*.jpg')
    # list_of_files = glob.glob('C:/Users/andye/PycharmProjects/BeerPiAWS/static/*.jpg')
    list_of_files.sort(key=os.path.getctime)
    latest_file = os.path.basename(list_of_files[current_pos - 1])
    logging.debug(f'get_latest_snap: {pos} {latest_file}')
    socketio.emit('set_latest_snap','static/'+latest_file)

# @socketio.on('get_latest_vid')
# def get_latest_vid():
#     list_of_files = glob.glob('/home/bitnami/htdocs/static/*.mp4')
#     # list_of_files = glob.glob('C:/Users/andye/Documents/static/*.mp4')
#     latest_file = os.path.basename(max(list_of_files, key=os.path.getctime))
#     logging.debug(f'get_latest_vid: static/{latest_file}')
#     socketio.emit('set_latest_vid','static/'+latest_file)

# Called from the PRi every time the temp is updated
@socketio.on("set_time_last_updated")
def set_time_last_updated(datetime_str):
    global req_update_period, req_temp
    # store this value in the data file
    _write_save_data(req_temp, req_update_period, datetime_str)
    socketio.emit("set_UI_last_updated",datetime_str)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
