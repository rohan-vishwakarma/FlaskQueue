import os
from celery import Celery
from dotenv import load_dotenv
load_dotenv()

os.environ["FORKED_BY_MULTIPROCESSING"] = "1"
from app import create_app

def create_celery_app():
    app = create_app()
    celery = Celery(
        app.import_name,
        broker_url=os.getenv('CELERY_BROKER_URL'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND'),
        serialize_type=os.getenv('CELERY_SERIALIZE_TYPE')
    )
    celery.conf.beat_schedule = {
        'add-every-30-seconds' : {
            'task' : 'app.tasks.updates',
            'schedule' : 5.0
        }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():  # Push Flask app context
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.autodiscover_tasks(["app.tasks"])  # Auto-discover tasks
    celery.autodiscover_tasks(['app.celerytask.tasks'])
    import app.celerysignals
    return celery

celery_app = create_celery_app()
