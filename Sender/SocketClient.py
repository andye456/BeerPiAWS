import logging
import socketio
from datetime import datetime
import subprocess
import requests, json
from time import gmtime, strftime, time
import time
import RPi.GPIO as GPIO
from threading import Thread
import traceback

# logging.basicConfig(filename='client.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# logger = logging.getLogger(__name__)
# logger.setLevel('DEBUG')

sio = socketio.Client()

print("SocketIO Client")
print("---------------")

# Global variables

# Temperature limits
desired_temp = ""
last_updated_time = ""
upper_bound = 0.0
lower_bound = 0.1

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

logging.basicConfig(level=logging.DEBUG)

# This is a 'global' - done as a mutable (right way to do it)
relay_1_state = {'isRelayOn': False}
relay_2_state = {'isRelayOn': False}
relay_3_state = {'isRelayOn': False}
relay_4_state = {'isRelayOn': False}

remote = '18.168.124.146'

@sio.event
def connect():
    logging.info('Connection estabished')

# This is called by the Server when the server receives get_temp_from_pi from the web page
# The function is also called by the main loop
@sio.on("get_temp")
def get_temp():
    logging.debug("Getting temp")
    temp1, temp2 = _read_temp_probe()
    temp1 = float(temp1)
    temp2 = float(temp2)
    sio.emit('set_temp_from_probes', {"t1": temp1, "t2": temp2})
    # Sends the current time to the SocketServer which then persists it and sends it on to the UI
    sio.emit('set_time_last_updated', datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))

# This is called by the SocketServer to set the update period
@sio.on("set_update_period")
def set_update_period(time_seconds):
    # Sets the the read frequency of the temperature probe
    logging.debug(f"Setting the update period to: {time_seconds}")
    global update_period, desired_temp
    update_period = int(time_seconds)

# Called by html to set the required temperature
@sio.on("set_required_temp")
def set_required_temp(required_temp):
    logging.debug(f"Setting required temp to: {required_temp}")
    global desired_temp
    desired_temp = int(required_temp)


# This turns the relay on for a certain amount of time
@sio.on("set_relay_state")
def set_relay_state(relay_states):
    logging.debug(relay_states)
    # If there is a value in the timeout field then turn the relay on in a thread that times out
    if relay_states['2']['timeout'] != '0' and relay_states['2']['timeout'] != '':
        if relay_states['2']['state']:
            Thread(target=set_relay_timeout, args=(2,relay_states['2']['timeout'],)).start()
    else:
        _set_relay_on("RLY2", relay_states['2']['state'])

    if relay_states['3']['timeout'] != '0' and relay_states['3']['timeout'] != '':
        if relay_states['3']['state']:
            Thread(target=set_relay_timeout, args=(3,relay_states['3']['timeout'],)).start()
    else:
        _set_relay_on("RLY3",relay_states['3']['state'])

    if relay_states['4']['timeout'] != '0' and relay_states['4']['timeout'] != '':
        if relay_states['4']['state']:
            Thread(target=set_relay_timeout, args=(4,relay_states['4']['timeout'],)).start()
    else:
        _set_relay_on("RLY4",relay_states['4']['state'])

def set_relay_timeout(rly, timeout):
    logging.debug(f'set_relay_{rly}_timeout {timeout}')
    _set_relay_on(f"RLY{rly}", True)
    time.sleep(int(timeout))
    _set_relay_on(f"RLY{rly}", False)
    get_relay_state()


@sio.on("camera")
def camera(cmd):
    logging.debug(f"camera called to take {cmd}")
    if cmd == "photo":
        photo = _take_photo()
        _scp_file(photo)
    elif cmd == "video":
        video = _take_video()
        _scp_file(video)

# This is called upon connection to the SocketServer and causes the state to be emitted to the UI
@sio.on("get_relay_state")
def get_relay_state():
    sio.emit('update_relay_state', {"1": {"state": relay_1_state['isRelayOn']},
                                    "2": {"state": relay_2_state['isRelayOn']},
                                    "3": {"state": relay_3_state['isRelayOn']},
                                    "4": {"state": relay_4_state['isRelayOn']}})

# This is set by an emit fro the server on startup top make sure the temperature aligns with what is in the GUI
@sio.on("update_req_period")
def set_update_period(value):
    global update_period
    update_period = value

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
        logging.warning('IndexError........')
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
        # This is only done here as the state of RLY1 is controlled by the client when the heater needs to be on/off
        sio.emit('update_relay_state', {"1": {"state": relay_1_state['isRelayOn']},
                                        "2": {"state": relay_2_state['isRelayOn']},
                                        "3": {"state": relay_3_state['isRelayOn']},
                                        "4": {"state": relay_4_state['isRelayOn']}})
    if relay == "RLY2":
        relay_2_state['isRelayOn'] = state
    if relay == "RLY3":
        relay_3_state['isRelayOn'] = state
    if relay == "RLY4":
        relay_4_state['isRelayOn'] = state

    logging.debug(f'Turning {relay} {state}')
    # Seems a bit weird that passing false to the output sends it high - so invert it
    state = not state
    # relay here needs to be the number not the name of the relay
    GPIO.output(eval(relay), state)

# Turns R1 on and off depending on the desired temp - reads temp every second
def control_temp_relay():
    while True:
        try:
            current_temp = _read_temp_probe()[0] # This is only for relay 1
        except TypeError:
            pass
        logging.debug(f"control_temp_relay::current_temp = {str(current_temp)}")
        logging.debug("control_temp_relay::dtemp  = "+str(desired_temp))
        logging.debug(f"relay_1_state['isRelayOn'] {relay_1_state['isRelayOn']}")
        if current_temp <= float(desired_temp) - lower_bound and not relay_1_state['isRelayOn']:
            _set_relay_on("RLY1", True)
        elif current_temp >= float(desired_temp) + upper_bound and relay_1_state['isRelayOn']:
            _set_relay_on("RLY1", False)
        time.sleep(1) # This is always 1 second as we want to keep the water temp accurate

def send_temp_to_server():
    while True:

        get_temp()
        logging.debug(f'Sleeping for {update_period} seconds')
        sleep_time = update_period
        for i in range(int(sleep_time)):
            # Check if the sleep time is still the update period, if update_period has been changed in the UI then this
            # loop will break and the new update period will be used.
            if sleep_time == update_period:
                time.sleep(1)
            else:
                break

def _take_photo():
    logging.debug("TAKING PHOTO")
    today = datetime.now()
    date_string = today.strftime("%d.%m.%Y-%H.%M.%S")
    # photo_name = '/home/pi/Pictures/snap.jpg'
    photo_name = f'/home/pi/Pictures/snap-{date_string}.jpg'
    width = "640"
    height = "480"
    try:
        subprocess.run(['/usr/bin/raspistill', '-o', photo_name, '-w', width, '-h', height, '-t', '1000'])
    except FileNotFoundError as f:
        logging.debug(">>>>> TAKE PHOTO"+photo_name)
    return photo_name

def _take_video():
    # raspivid -o Videos/test200K.h264 -t 5000 -w 640 -h 480 -fps 10 -b 200000 -a 12
    today = datetime.now()
    date_string = today.strftime("%d.%m.%Y-%H.%M.%S")
    video_dir='/home/pi/Videos'
    raw_name = video_dir+'/vid.h264'
    # video_name = video_dir+'/vid.mp4'
    video_name = f'{video_dir}/vid-{date_string}.mp4'
    logging.info("TAKING VIDEO")
    width = "640"
    height = "480"
    vid_time = "5000"
    fps = "10"
    bandwidth = "200000"
    try:
        subprocess.run(['/usr/bin/raspivid', '-o', raw_name, '-t', vid_time, '-w', width, '-h', height, '-fps', fps, '-b', bandwidth, '-a', '12'])
        # Convert video into mp4
        subprocess.run(['MP4Box', '-add', raw_name, video_name, '-new'])
    except FileNotFoundError as f:
        logging.info(">>>>> TAKE VIDEO"+video_name)
    return video_name

def _scp_file(file):
    username="bitnami"
    # remote="35.176.56.125"
    # remote="localhost"
    # dir="/opt/bitnami/apache2/htdocs/static"
    dir="/home/bitnami/BeerPiAWS/Receiver/static/picture_files"
    logging.info(f"Sending file {file} to {username}@{remote}:{dir}")

    try:
        subprocess.run(['/usr/bin/scp', '-i', '/home/pi/LightsailDefaultKey-eu-west-2.pem', file, username+"@"+remote+":"+dir])
    except FileNotFoundError as f:
        logging.debug('/usr/bin/scp -i /home/pi/LightsailDefaultKey-eu-west-2.pem '+ file+" "+ username+"@"+remote+":"+dir)

def dissconnect():
    logging.info('diconnected')


if __name__ == "__main__":
    logging.info("Connecting to server")
    sio.connect(host)
    # uses the temperature to control the main relay
    Thread(target=control_temp_relay).start()
    Thread(target=send_temp_to_server).start()


