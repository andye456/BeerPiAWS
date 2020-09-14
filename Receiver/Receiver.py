from flask import Flask, request, render_template
import logging, json
from time import gmtime, strftime

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

tempObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'n/a'}
timeout = {'timeout':"1"}

temp =  {'temp':"25"}

@app.route('/receiver', methods=['POST', 'GET'])
def receiver():
    if request.method == 'POST':
        req_data = request.get_json()
        global tempObj
        tempObj = json.loads(req_data)
        print(tempObj['temperature'])
        logging.warning(tempObj['isrelayon'])
        return tempObj
    if request.method == 'GET':
        return tempObj
        # return f'<h1>Current temp: {str(tempObj["temperature"])}</h1>'

# This returns the html page when /latest is called by the client
@app.route('/latest')
def index():
    return render_template('current_temp.html')

# gets the update period value from the webpage
@app.route('/get_interval')
def get_interval():
    global timeout
    logging.info("********* get_interval called *********")
    logging.info(f"********* {timeout} *********")
    return timeout

@app.route('/get_temp')
def get_temp():
    global temp
    logging.info("********* get_temp called *********")
    logging.info(f"********* {temp} *********")
    return temp

@app.route('/set_interval', methods=['POST'])
def set_interval():
    t = request.data
    logging.info("********* set_interval called *********")
    logging.debug(t)
    global timeout
    timeout = json.loads(t)
    print(f"********* {timeout} *********")
    return timeout

@app.route('/set_temp',methods=['POST'])
def set_temp():
    tp = request.data
    logging.info("********* set_temp called *********")
    logging.debug(tp)
    global temp
    temp = json.loads(tp)
    print(f"********* {temp} *********")
    return temp


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8081)
    app.run(host='localhost', port=8081)
