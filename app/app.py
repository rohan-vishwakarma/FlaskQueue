import sys, os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from flask import Flask
from routes import bp

app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url=os.getenv('CELERY_BROKER_URL'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND'),
        task_ignore_result=os.getenv('TASK_IGNORE_RESULT'),
        timezone=os.getenv('CELERY_TIME_ZONE'),
        enable_utc=os.getenv('CELERY_ENABLE_UTC'),
        result_backend_table_names= {
            "task": "myapp_taskmeta",
            "group": "myapp_groupmeta",
        }
    ),
)

app.config.from_mapping()


if __name__ == '__main__':
    app.run(port=5000, debug=True)