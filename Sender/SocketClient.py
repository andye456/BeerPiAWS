import logging
import socketio

logging.basicConfig(level=logging.WARNING)

# logger = logging.getLogger(__name__)
# logger.setLevel('DEBUG')

sio = socketio.Client()

print("SocketIO Client")
print("---------------")

@sio.event
def connect():
    logging.info('Connection estabished')

@sio.on('message')
def my_message(num):
    logging.warning(f'>>>>>>>>>>>> message received with {num}')
    # sio.emit('my response', {'response': 'my response'})

@sio.event
def dissconnect():
    logging.info('diconnected')

sio.connect('http://35.176.56.125:5000')
logging.info('Sending message')
sio.emit("my_message", "TEST MESSAGE!")

