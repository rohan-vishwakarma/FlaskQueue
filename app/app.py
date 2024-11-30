import sys
from pathlib import Path


# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from flask import Flask
from routes import bp

app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url="pyamqp://guest@localhost//",
        result_backend="db+mysql://root@localhost/flask_queue",
        task_ignore_result=False,
        timezone="Asia/Kolkata",
        enable_utc=False,
        result_backend_table_names= {
            "task": "myapp_taskmeta",
            "group": "myapp_groupmeta",
        }
    ),
)

app.config.from_mapping()


if __name__ == '__main__':
    app.run(port=5000, debug=True)