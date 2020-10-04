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


# Web Sockets
You can poll end-points for updates that are  made from 
web page input, but this is very chatty and the RPi is polling the AWS server every second 

A better way is to use Web Sockets, or more specifically, socket.io. Socket.io implements WebSockets
if it can, otherwise it defaults to a polling type algorithm. Anyway what this means is that the 
data is sent to the RPi, using the connection established by the RPi, only when it is needed. This will 
cut down on the data that is exchanged with the AWS server.

### Server (AWS)
Flask_socketio

https://flask-socketio.readthedocs.io/en/latest/

### Client (RPi)
python-socketio

https://python-socketio.readthedocs.io/en/latest/client.html

Supports Client side socket.io to connect to the Server.

### UI
This is a standard HTML page stored in htdocs on AWS

It uses socket.io in javascript to comunicate with the SocketIO server.

### Connection
* The RPi makes a connection to the http address of the socket.io Server
* The Server then returns data to the socket.io receiver running on the RPi

It's as simple as that.

![](beer_pi.png)
