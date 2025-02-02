import sys
from pathlib import Path

from click import progressbar
from sqlalchemy.exc import SQLAlchemyError
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.models import CeleryTask, db
from app import create_app
from datetime import datetime
import json, traceback
from celery.signals import task_prerun, task_postrun, task_failure, task_retry, task_success, task_internal_error, worker_shutdown

app = create_app()

class StatusEnum:
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'

@task_prerun.connect
def task_sent_handler(task, task_id, *args, **kwargs):
    queue_name = task.request.delivery_info.get('routing_key', 'unknown')
    with app.app_context():
        args_serialized = json.dumps(kwargs['args'])
        try:
            new_task = CeleryTask(
                task_id=task_id,
                task_name=task.name,
                args=args_serialized,
                kwargs=kwargs['kwargs'],
                queue = queue_name,
                progress=0,
                status=StatusEnum.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(new_task)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating task record: {e}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, state=None, retval=None, *args, **kwargs):
    """Triggered after the task finishes."""
    with app.app_context():
        task = db.session.query(CeleryTask).filter_by(task_id=task_id).first()
        if task:
            task.result = str(retval) if retval else None
            task.state = state
            task.updated_at = datetime.utcnow()
            db.session.commit()

@task_success.connect
def task_completed_handler(sender, result, *args, **kwargs):
    task_id = sender.request.id
    with app.app_context():
        try:
            task_record = CeleryTask.query.filter_by(task_id=task_id).first()
            if task_record:
                task_record.status = StatusEnum.SUCCESS
                task_record.updated_at = datetime.now()
                task_record.result = result
                db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating task record on completion: {e}")

@task_failure.connect
def task_failed_handler(task_id, exception, *args, **kwargs):
    with app.app_context():
        try:
            task_record = CeleryTask.query.filter_by(task_id=task_id).first()
            if task_record:
                task_record.status = StatusEnum.FAILURE
                task_record.updated_at = datetime.now()
                db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating task record on failure: {e}")

@task_internal_error.connect
def task_internal_error(task_id, args, kwargs, einfo, **extra_kwargs):
    with app.app_context():
        try:
            task_record = CeleryTask.query.filter_by(task_id=task_id).first()
            if task_record:
                task_record.status = StatusEnum.FAILURE
                task_record.updated_at = datetime.now()
                db.session.commit()
                print(f"Task {task_id} status updated to FAILURE.")
            else:
                print(f"No record found for task_id: {task_id}")
        except SQLAlchemyError as db_error:
            db.session.rollback()
            print(f"Database error for task_id {task_id}: {db_error}")
        except Exception as e:
            print(f"Unexpected error in task_internal_error_handler: {e}")
            traceback.print_exc()
        finally:
            # Log traceback information for debugging
            print(f"Traceback for task_id {task_id}: {einfo.traceback}")


@task_retry.connect
def task_retry_handler(task_id, *args, **kwargs):
    with app.app_context():
        try:
            task_record = CeleryTask.query.filter_by(task_id=task_id).first()
            if task_record:
                task_record.status = StatusEnum.RETRY  # Mark task as RETRY
                task_record.retries += 1  # Increment the retries count
                task_record.updated_at = datetime.now()  # Update the timestamp
                db.session.commit()  # Commit the changes to the database
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating task record on retry: {e}")


@worker_shutdown.connect
def on_worker_shutdown(sig, how, exitcode, **kwargs):
    from celery.result import AsyncResult

    # Fetch the list of active tasks
    active_tasks = app.control.inspect().active()
    if active_tasks:
        for worker, tasks in active_tasks.items():
            for task in tasks:
                task_id = task['id']
                result = AsyncResult(task_id)
                if result.state in ['PENDING', 'STARTED']:
                    result.update_state(state='FAILURE', meta={'exc_message': 'Worker shutdown'})



