from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .routes import bp
from .models import db
from flask_restful import Api
from app.controllers import Etl
import os
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
    app.register_blueprint(bp)
    api = Api(app)
    api.prefix = '/api'
    api.add_resource(Etl.Extract, '/etl/extract')
    db.init_app(app)
    with app.app_context():
        from .models import Products
        db.create_all()
    return app
