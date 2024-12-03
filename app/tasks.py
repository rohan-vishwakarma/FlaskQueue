import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import time
from app.celery_app import celery_app
from .models import Products
from app import create_app
app = create_app()


@celery_app.task
def add(x, y):
    print("Task Started By rohan")
    time.sleep(10)

    # Push the Flask app context for database queries
    with app.app_context():
        product = Products.query.first()
        if not product:
            print("No products found!")
            return "No products available."

        print("Successfully Completed with")
        print(product.name)
        return product.name

@celery_app.task
def sub(x, y):
    return x - y


@celery_app.task
def updates():
    return "Updates Completed With Schedular"


