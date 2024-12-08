import os
from celery import Celery
from dotenv import load_dotenv
from kombu import Queue
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
    # Configure Celery queues and routing
    celery.conf.task_queues = (
        Queue('flask@default', routing_key='flask@default'),
        Queue('flask@testing', routing_key='flask@testing.#'),
        Queue('flask@process-csv', routing_key='flask@process-csv')
    )
    celery.conf.task_default_queue = 'flask@default'
    celery.conf.task_default_exchange = 'flask@default'
    celery.conf.task_default_routing_key = 'flask@default'
    celery.conf.task_routes = {
        'app.tasks.add': {'queue': 'flask@default'},
        'app.tasks.sub': {'queue': 'flask@default'},
        'app.tasks.updates': {'queue': 'flask@testing'},
        'app.celerytask.tasks.processCsv': {'queue': 'flask@process-csv'}
    }

    # Set serializers
    celery.conf.task_serializer = os.getenv('CELERY_SERIALIZE_TYPE', 'json')
    celery.conf.result_serializer = os.getenv('CELERY_SERIALIZE_TYPE', 'json')
    celery.conf.accept_content = [os.getenv('CELERY_SERIALIZE_TYPE', 'json')]


    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():  # Push Flask app context
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.autodiscover_tasks(['app.tasks', 'app.celerytask.tasks'])
    import app.celerysignals
    return celery

celery_app = create_celery_app()
