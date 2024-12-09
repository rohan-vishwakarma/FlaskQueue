import os

from marshmallow import ValidationError

current_path = os.getcwd()
from flask import Blueprint, render_template
bp = Blueprint('bp', '__name__', template_folder='frontend', static_folder='frontend/dashbrd/assets')
from .models import Products, db, CeleryTask, Dataset


@bp.route('/', methods=['GET'])
def index():
    return render_template('dashbrd/index.html')

@bp.route('/jobs', methods=['GET'])
def jobs():
    return render_template('dashbrd/job/jobs.html')

@bp.route('/job/running', methods=['GET'])
def jobsList():
    try:
        tasks = (
            db.session.query(CeleryTask)
            .outerjoin(Dataset, CeleryTask.task_id == Dataset.task_id)
            .order_by(CeleryTask.created_at.desc(), Dataset.created_at.desc())
            .all()
        )

        tasks_data = [task.to_dict() for task in tasks]

        return render_template('dashbrd/job/joblist.html', data=tasks_data)

    except ValidationError as err:
        return {"errors": err.messages}, 400
    except Exception as ex:
        return {"errors": str(ex)}, 500

@bp.route('/job/new', methods=['GET'])
def jobsNew():
    return render_template('dashbrd/job/jobnew.html')