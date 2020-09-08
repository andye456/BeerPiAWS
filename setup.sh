#!/bin/bash
# Change the target address from localhost to AWS IP address
AWS_IP="35.176.56.125"
sed -i s/localhost/35.176.56.125/ Sender/RPiData.py
# Change the webserver address to 0.0.0.0
sed -i s/localhost/0.0.0.0/ Receiver/Receiver.py
# Change the requirements to ref the correct version of RPi.GPIO
sed s/.*GPIO.*/RPi.GPIO==0.7.0/ requirements.txt
# Change the test temp file to the real one
sed -i s/.*Temp_File.*/Temp_File = "/sys/bus/w1/devices/28-01193c3b3149/w1_slave"/ Sender/RPiData.py
# Check the version of python avilable
echo `which python3`
# create the virtual env
if [[ `python -V | grep 2.7` ]]
then
  python3 -m venv venv
else
  [[ -r /usr/local/bin/python3.6 ]] &&  /usr/local/bin/python3.6 -m venv venv
fi
. venv/bin/activate
pip install -r requirements.txt
