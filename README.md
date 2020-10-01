# BeerPiAWS
### Beer Temperature monitor and heater control
###### AWS version of BeerPi
* Python script reads temperature data from a temperature probe attached to a Raspberry Pi
* Json string, {"timestamp":...., "temperature": 21.5} written to Mongo DB on AWS every 10 minutes
* D3 web page reads the data and displays the trend in a graph with data points every 10 minutes
* JQuery web page shows the current temperature, can be set to auto update every n seconds.

## Installing Python 3.8 and SSL
Follow the guidance here:

https://help.dreamhost.com/hc/en-us/articles/115000702772-Installing-a-custom-version-of-Python-3

(and https://help.dreamhost.com/hc/en-us/articles/360001435926-Installing-OpenSSL-locally-under-your-username)

## HOW TO
### Add a function controlled by the HTML page
#### In `current_temp.html`
* Add some html to make a new input
```html
<div>
    <input type="submit" class="btn btn-primary" id="photo1">
    <label  for="image1">Still Image</label>
```
* Create a function that is called by using the input
```javascript
// The photo/video buttons
$('#photo1').click(function() {
    // Either call code directly or make a function call here
    camera("photo");
});
```
* Add an ajax call inside the function (camera(type) in this case)
```javascript
$.ajax({
    type: 'POST',
    url: '/camera/'+type,
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify({take: type}),
    success: function (data, status) {
        console.log(data)
    },
    error: function (status) {
        console.log("error " + status);
    }
});

```
#### In `Receiver.py` running on AWS
* Create a route to accept the AJAX call from the web page (/camera)
```python
@app.route('/camera/<type>', methods=['POST'])
def set_camera(type):
    global camera_type
    camera_type = type
    # set the "take a photo or video" variable
```
    
* create another route to get the photo or video when requested by the RPi
```python
@app.route('/get_camera'):
def get_camera():
    global camera_type
    camera_type = None
    return '{take: "photo"}' # or 'video'
```

* (Optional) create another route that can be called by the RPi to send the data back from the RPi
```python
@app.route('/send_data')
def send_data():
    #Do some update or whatever
```
    

#### In `RPiData.py` running on the RPi
* Create a function that calls the "get_" endpoint in Receiver.py 
```python
def get_camera():
    while True:
        state = requests.get("http://1.2.3.4:8081/get_camera")
        _do_stuff()
        time.sleep(1)
```

* Create a function that returns the data/image or whatever back to the receiver.

This can go in the _do_stuff() function.
```python
# POSTs the data to the receiver on AWS
def _send_data(json_data):
    try:
        r = requests.post(send_url, json=json_data)
        return r.status_code
    except ConnectionRefusedError as e:
        logging.error("connection refused")
```

# Web Sockets
### Rewrite
The above method up to now has been OK, polling the server for updates that are  made from 
web page input, but this is very chatty and the RPi is polling the AWS server every second for 
updates.

A better way is to use Web Sockets, or more specifically, socket.io. Socket.io implements WebSockets
if it can, otherwise it defaults to a polling type algorithm. Anyway what this means is that the 
data is sent to the RPi, using the connection established by the RPi, only when it is needed. This will 
cut down on the data that is exchanged with the AWS server.

### Server (AWS)
Flask_socketio

https://flask-socketio.readthedocs.io/en/latest/

This is chosen as it supports web page endpoints as per the existing code
### Client (RPi)
python-socketio

https://python-socketio.readthedocs.io/en/latest/client.html

Supports Client side socket.io to connect to the Server.

### Connection
* The RPi makes a connection to the http address of the socket.io Server
* The Server then returns data to the socket.io receiver running on the RPi

It's as simple as that.

## HOW TO:
What are the changes that are to be made to existing code.

 1. Keep the Web Page end points, but remove the setting of globals for the relay states 
 (unless state needs to be maintained)
 2. Remove all the end points that were polled by the RPi for updates.
 3. In the web endpoints add emit functions to send data to the socket.io receivers on the RPi.
