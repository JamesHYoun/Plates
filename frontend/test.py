import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.event
def updateGame(data):
    print('Received updateGame:', data)

sio.connect('http://localhost:8000/socket.io')
sio.emit('updateToServer', {'num': 0})