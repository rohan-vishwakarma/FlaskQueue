from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .routes import bp
from .models import db
from flask_restful import Api
from app.controllers import Etl

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Rohan%401234@localhost/flask_celery_etl'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SECRET_KEY"] = "your-secret-key"
    app.register_blueprint(bp)

    api = Api(app)
    api.prefix = '/api'
    api.add_resource(Etl.Extract, '/etl/extract')

    db.init_app(app)
    with app.app_context():
        from .models import Products
        db.create_all()
    return app
