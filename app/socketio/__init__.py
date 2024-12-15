from flask_socketio import SocketIO, emit, join_room

# Initialize SocketIO
socketio = SocketIO()

@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    emit('message', {'data': 'Hello, Client!'})

@socketio.on('join', namespace='/job/running')
def on_join(data):
    join_room("celerytask")
    emit('joined', {'msg': f'Joined room: Celery Task'}, room="celerytask")


@socketio.on('disconnect')
def handle_disconnect():
    print("A user has disconnected.")

@socketio.on('custom_event')
def handle_custom_event(data):
    print('Received custom_event with data:', data)
    emit('response', {'data': 'Custom event response'})
