from flask import Flask, request
import logging, json

app = Flask(__name__)


tempObj = 'n/a'
@app.route('/receiver', methods=['POST', 'GET'])
def receiver():
    if request.method == 'POST':
        req_data = request.get_json()
        global tempObj
        tempObj = json.loads(req_data)
        logging.warning(tempObj['temperature'])
        return tempObj
    if request.method == 'GET':
        return f'<h1>Current temp: {tempObj["temperature"]}</h1>'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
