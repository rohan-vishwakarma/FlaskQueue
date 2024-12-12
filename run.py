from app import create_app, socketio


app = create_app()

app.app_context().push()
if __name__ == "__main__":
    socketio.run(app, debug=True)
