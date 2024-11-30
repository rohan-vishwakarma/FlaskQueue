from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .routes import bp
from .models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/flask_queue'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SECRET_KEY"] = "your-secret-key"

    app.register_blueprint(bp)

    db.init_app(app)
    with app.app_context():
        from .models import Products
        db.create_all()
    return app
