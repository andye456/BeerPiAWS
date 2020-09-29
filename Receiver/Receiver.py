from flask import Flask, request, render_template
import logging, json
from time import gmtime, strftime

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

tempObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'n/a'}
timeout = {'timeout':"1"}

temp =  {'temp':"25"}
relay_state= {"2": {"state": False}, "3": {"state": False}, "4": {"state": False}}

camera_type = {"cmd":None}

@app.route('/receiver', methods=['POST', 'GET'])
def receiver():
    if request.method == 'POST':
        req_data = request.get_json()
        global tempObj
        tempObj = json.loads(req_data)
        logging.warning(tempObj['isrelayon'])
        return tempObj
    if request.method == 'GET':
        return tempObj
        # return f'<h1>Current temp: {str(tempObj["temperature"])}</h1>'

# This returns the html page when /latest is called by the client
@app.route('/')
def index():
    logging.debug("++++++++++++++++++++++"+app.root_path)
    return render_template('current_temp.html')

# gets the update period value from the webpage
@app.route('/get_interval')
def get_interval():
    global timeout
    logging.debug("********* get_interval called *********")
    logging.info(f"/get_interval timeout = {timeout}")
    return timeout

@app.route('/get_temp')
def get_temp():
    global temp
    logging.debug("********* get_temp called *********")
    logging.info(f"/get_temp {temp} ")
    return temp

# This get the state of all the relays, the state is a global variable held in this script
@app.route('/get_current_status')
def get_current_status():
    logging.debug(f"current_state {str(relay_state['2']['state'])},{str(relay_state['3']['state'])},{str(relay_state['4']['state'])}")
    return f"{str(relay_state['2']['state'])},{str(relay_state['3']['state'])},{str(relay_state['4']['state'])}"

@app.route('/set_interval', methods=['POST'])
def set_interval():
    t = request.data
    logging.debug("********* set_interval called *********")
    logging.debug(t)
    global timeout
    timeout = json.loads(t)
    return timeout

# Sets the relay from the checkboxes on the front page
@app.route('/set_relay/<num>', methods=['POST'])
def set_relay(num):
    global relay_state
    st = json.loads(request.data)
    relay_state[num]['state']=st['state']
    logging.debug(f"+=+=+=+=+=+=+= {request.data} set_relay {num} {relay_state}")
    return relay_state[num]

# get the relay states
@app.route('/get_relay/<num>', methods=['GET'])
def get_relay(num):
    global relay_state

    if num == 2:
        logging.debug(f"************ get_relay::relay_state = {relay_state['2']}")
        return relay_state['2']
    if num == 3:
        logging.debug(f"************ get_relay::relay_state = {relay_state['3']}")
        return relay_state['3']
    if num == 4:
        logging.debug(f"************ get_relay::relay_state = {relay_state['4']}")
        return relay_state['4']
    return relay_state


@app.route('/set_temp',methods=['POST'])
def set_temp():
    tp = request.data
    logging.debug(tp)
    global temp
    temp = json.loads(tp)
    return temp

@app.route('/set_camera/<type>', methods=['POST'])
def set_camera(type):
    global camera_type
    camera_type['cmd'] = type
    return camera_type['cmd']

# Called by the RPi to get the camera photo request that has been set from the web page.
@app.route('/get_camera', methods=['GET'])
def get_camera():
    logging.debug("************ get_camera ************")
    global camera_type
    logging.debug(camera_type)
    cpy = camera_type.copy()
    logging.debug(cpy)
    # Reset the camera command so that multiple photos aren't taken
    camera_type['cmd'] = None
    logging.debug(camera_type)
    logging.debug(cpy)

    return cpy

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8081)
    app.run(host='localhost', port=8081)

