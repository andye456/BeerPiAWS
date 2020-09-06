from flask import Flask, request, render_template
import logging, json
from time import gmtime, strftime

app = Flask(__name__)


tempObj = {'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'temperature':f'n/a'}
timeout = {'timeout':"1"}

@app.route('/receiver', methods=['POST', 'GET'])
def receiver():
    if request.method == 'POST':
        req_data = request.get_json()
        global tempObj
        tempObj = json.loads(req_data)
        logging.warning(tempObj['temperature'])
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
    print("********* get_interval called *********")
    print(f"********* {timeout} *********")
    return timeout

@app.route('/set_interval', methods=['POST'])
def set_interval():
    t = request.data
    print("********* set_interval called *********")
    global timeout
    timeout = json.loads(t)
    print(f"********* {timeout} *********")
    return timeout

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8081)
    app.run(host='127.0.0.1', port=8081)
