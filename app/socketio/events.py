from flask_socketio import emit


def setup_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        # Send a greeting message when a client connects
        emit('task_progress_update', {'data': 'Hello, Client!'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print("A user has disconnected.")

    # You can define other event handlers here, such as message handling
    @socketio.on('custom_event')
    def handle_custom_event(data):
        print('Received custom_event with data:', data)
        emit('response', {'data': 'Custom event response'})
