from app.celery_app import celery_app
from app.app import app
if __name__ == "__main__":
    with app.app_context():
        celery_app.start()