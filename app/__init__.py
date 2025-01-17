from mimetypes import inited

from flask import Flask
from .routes import bp
from .models import db
from flask_restful import Api
from app.controllers import etl
import os
from dotenv import load_dotenv
from app.socketio import socketio
load_dotenv()




def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
    app.register_blueprint(bp)
    api = Api(app)
    api.prefix = '/api'
    api.add_resource(etl.Extract, '/etl/extract')
    socketio.init_app(app, cors_allowed_origins=["http://127.0.0.1:5000", "http://localhost:5000"])


    db.init_app(app)
    with app.app_context():
        from .models import Products
        db.create_all()
    return app
