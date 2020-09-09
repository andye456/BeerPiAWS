#!/bin/bash
# Change the target address from localhost to AWS IP address
sed -i s/localhost/35.176.56.125/ Sender/RPiData.py
# Change the webserver address to 0.0.0.0
sed -i s/localhost/0.0.0.0/ Receiver/Receiver.py
# Change the requirements to ref the correct version of RPi.GPIO
sed -i s/.*GPIO.*/RPi.GPIO==0.7.0/ requirements.txt
# Change the test temp file to the real one
sed -i 's/w1_slave/\/sys\/bus\/w1\/devices\/28-01193c3b3149\/w1_slave/' Sender/RPiData.py
# change the localhost int he html to pevent CORS error
sed -i s/localhost/35.176.56.125/ Receiver/templates/current_temp.html
# Check the version of python avilable
echo `which python3`
# create the virtual env
if [[ -r /usr/local/bin/python3.6 ]]
then
  echo "Using python /usr/local/bin/python3.6"
  /usr/local/bin/python3.6 -m venv venv
else
  echo " using python3"
  python3 -m venv venv
fi
echo "Switching to venv"
. venv/bin/activate
if [[ $? -eq 0 ]]
then
  pip install -r requirements.txt
else
  echo "something went wrong"
  exit 1
fi
