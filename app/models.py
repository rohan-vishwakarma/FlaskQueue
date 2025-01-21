import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import ENUM, CHAR
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
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
    state = db.Column(db.Text, nullable=True)
    progress = db.Column(db.Float, nullable=False)
    result = db.Column(db.Text, nullable=True)  # Result of the task
    error_message = db.Column(db.Text, nullable=True)  # Error message if the task failed
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)  # When the task was created
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)  # Last update time
    datasets = relationship('Dataset', backref='celery_tasks', passive_deletes=True)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'args' : self.args,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'datasets': [dataset.to_dict() for dataset in self.datasets]  # Serialize related datasets
        }

    def __repr__(self):
        return (f"<CeleryTask(id={self.id}, task_id={self.task_id}, "
                f"task_name={self.task_name}, status={self.status}, queue={self.queue})>")


class Dataset(db.Model):

    __tablename__ = "dataset"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(CHAR(36), ForeignKey('celery_tasks.task_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When the task was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # Last update time

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def insert(name, taskId):
        try:
            # Create a new Dataset instance
            new_dataset = Dataset(name=name, task_id=taskId)
            db.session.add(new_dataset)
            db.session.commit()
            return new_dataset  # Optionally return the created object
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting dataset: {e}")
        finally:
            db.session.close()

    @staticmethod
    def count():
        try:
            count = Dataset.query.count()
            if count is None or count == 0:
                return 1
            return count + 1
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting dataset: {e}")
        finally:
            db.session.close()