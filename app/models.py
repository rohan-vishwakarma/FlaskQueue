from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import ENUM
from datetime import datetime

db = SQLAlchemy()

class Products(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    brand = db.Column(db.String(100))

statusEnum = ENUM('PENDING', 'STARTED', 'SUCCESS', 'FAILURE')

class CeleryTask(db.Model):
    __tablename__ = 'celery_tasks'

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for the task
    task_id = db.Column(db.String(255), nullable=False, unique=True)  # Celery's task ID (UUID)
    task_name = db.Column(db.String(255), nullable=False)  # Name of the task
    args = db.Column(db.Text, nullable=True)  # Positional arguments for the task (stored as JSON or stringified list)
    kwargs = db.Column(db.Text, nullable=True)  # Keyword arguments for the task (stored as JSON or stringified dict)
    queue = db.Column(db.String(255), nullable=True)  # The queue in which the task was placed
    retries = db.Column(db.Integer, nullable=True, default=0)  # Number of retries for the task
    status = db.Column(statusEnum, nullable=False, default='PENDING')  # Task status
    result = db.Column(db.Text, nullable=True)  # Result of the task
    error_message = db.Column(db.Text, nullable=True)  # Error message if the task failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When the task was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # Last update time

    def __repr__(self):
        return (f"<CeleryTask(id={self.id}, task_id={self.task_id}, "
                f"task_name={self.task_name}, status={self.status}, queue={self.queue})>")
