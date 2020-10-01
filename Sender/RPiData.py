import logging
from datetime import datetime
import subprocess
import requests, json
from time import gmtime, strftime
import time
import RPi.GPIO as GPIO
from threading import Thread
import traceback


temp_file1 = "w1_slave1"
temp_file2 = "w1_slave2"
host="http://localhost"
port="8081"
send_endpoint="receiver"
receive_endpoint = "get_interval"
temp_endpoint = "get_temp"
relay_endpoint = 'get_relay'
camera_endpoint = 'get_camera'

# Temperature limits
desired_temp = 28
margin = 0.1

send_url = f'{host}:{port}/{send_endpoint}'
get_url = f'{host}:{port}/{receive_endpoint}'
get_temp =  f'{host}:{port}/{temp_endpoint}'
get_relay_url = f'{host}:{port}/{relay_endpoint}'
camera = f'{host}:{port}/{camera_endpoint}'

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
        with open(temp_file1, "r") as f:
            lines = f.readlines()
            t1 = int(lines[1].split("=")[1])/1000
        with open(temp_file2, "r") as f:
            lines = f.readlines()
            t2 = int(lines[1].split("=")[1])/1000
        return t1,t2
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

# Reads the temp probe and creates a data object to send to the AWS receiver end point.
# Gets the relay state and reports it back to UI
# Gets the update period from the UI and updates the update period of the UI.
def temperature_control():
    while True:
        data,data2 = _read_temp_probe()
        data = float(data)
        data2 = float(data2)
        # Puts the current temp and timestamp into a JSON object.
        dataObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'{data:.2f}','temperature2':f'{data2:.2f}', 'isrelayon':relay_1_state['isRelayOn']}
        jsonObj = json.dumps(dataObj)
        logging.info(jsonObj)
        # Send data to the AWS server to display on the web page
        _send_data(jsonObj)
        # Get the update interval
        t = _get_data()
        for i in range(int(t)):
            time.sleep(1)

def control_temp_relay():
    while True:
        logging.debug(f"control_temp_relay::relay_1_state['isRelayOn'] {str(relay_1_state['isRelayOn'])}")
        current_temp = _read_temp_probe()[0] # This is only for relay 1
        logging.debug(f"control_temp_relay::current_temp = {str(current_temp)}")
        # global desired_temp
        dtemp = _get_required_temp()
        logging.debug("control_temp_relay::dtemp  = "+str(dtemp))
        if current_temp <= float(dtemp) - margin:
            _set_relay_on("RLY1", True)
        elif current_temp >= float(dtemp) + margin:
            _set_relay_on("RLY1", False)
        time.sleep(1)


def _take_photo():
    logging.debug("TAKING PHOTO")
    today = datetime.now()
    date_string = today.strftime("%d.%m.%Y-%H.%M.%S")
    photo_name = '/home/pi/Pictures/snap.jpg'
    # photo_name = '/home/pi/Pictures/snap-'+date_string+'.jpg'
    width = "640"
    height = "480"
    try:
        subprocess.run(['/usr/bin/raspistill', '-o', photo_name, '-w', width, '-h', height])
    except FileNotFoundError as f:
        logging.debug(">>>>> TAKE PHOTO"+photo_name)
    return photo_name

def _take_video():
    # raspivid -o Videos/test200K.h264 -t 5000 -w 640 -h 480 -fps 10 -b 200000 -a 12
    logging.debug("TAKING VIDEO")
    today = datetime.now()
    date_string = today.strftime("%d.%m.%Y-%H.%M.%S")
    video_dir='/home/pi/Videos'
    raw_name = video_dir+'/vid.h264'
    video_name = video_dir+'/vid.mp4'
    # video_name = video_dir+'/vid-'+date_string+'.h264'
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
    remote="35.176.56.125"
    dir="/home/bitnami/BeerPiAWS/Receiver/static"
    logging.info(f"Sending file {file} to {username}@{remote}:{dir}")

    try:
        subprocess.run(['/usr/bin/scp', '-i', '/home/pi/LightsailDefaultKey-eu-west-2.pem', file, username+"@"+remote+":"+dir])
    except FileNotFoundError as f:
        logging.debug('/usr/bin/scp -i /home/pi/LightsailDefaultKey-eu-west-2.pem '+ file+" "+ username+"@"+remote+":"+dir)


def get_camera():
    while True:
        logging.debug("GET: " + camera )
        camera_cmd = requests.get(camera)
        j = json.loads(camera_cmd.text)
        j['cmd']
        logging.debug(f".......................Command {j['cmd']}")
        if j['cmd'] == "photo":
            photo = _take_photo()
            _scp_file(photo)
        elif j['cmd'] == "video":
            video = _take_video()
            _scp_file(video)
        time.sleep(1)


if __name__ == '__main__':
    # gets the temperature from the temp probe in a thread
    Thread(target=temperature_control).start()
    # uses the temperature to control the main relay
    Thread(target=control_temp_relay).start()
    # reads the state of the check boxes and sets the other relays accordingly
    Thread(target=get_relay_state).start()
    # reads the camera requests
    Thread(target=get_camera).start()