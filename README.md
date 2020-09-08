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