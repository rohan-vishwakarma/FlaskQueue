import os
from marshmallow import ValidationError
from sqlalchemy import text

current_path = os.getcwd()
from flask import Blueprint, render_template, request, abort
bp = Blueprint('bp', '__name__', template_folder='frontend', static_folder='frontend/dashbrd/assets')
from .models import Products, db, CeleryTask, Dataset

@bp.route('/', methods=['GET', 'POST'])
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

@bp.route('/job/running/dataset/<uuid:jobUuid>', methods=['GET'])
def jobsDataset(jobUuid):
    try:
        params = request.args
        limit = 8 if not params.get('limit', 8) else int(params.get('limit', 8))
        page = 1 if not params.get('page', 1) else int(params.get('page', 1))

        celeryTask = db.session.query(Dataset.task_id, Dataset.name).filter_by(task_id=str(jobUuid)).first()
        print("celery task", jobUuid)
        if not celeryTask:
            abort(404, description="Job UUID not found in Dataset")

        dataset = celeryTask.name
        offset = (page - 1) * limit

        totalQuery = text(f"SELECT COUNT(*) FROM {dataset}")
        totalResult = db.session.execute(totalQuery)
        totalCount = totalResult.scalar()

        query = text(f"SELECT * FROM {dataset} LIMIT {limit} OFFSET {offset}")
        result = db.session.execute(query)
        columns = result.keys()
        rowsAsDict = [dict(zip(columns, row)) for row in result.fetchall()]
        currentCount = len(rowsAsDict)

        if currentCount == 0:
            return {"success": False, "message": "No Records Found"}, 404
        print("columns",list(columns))
        return render_template(
            'dashbrd/job/dataset.html',
            uuid=str(jobUuid),
            dataset=str(dataset),
            data={
                "success": True,
                "message": "The Request Proceeded",
                "data": rowsAsDict,
                "columns": list(columns),
                "meta": {
                    "limit": limit,
                    "page": page,
                    "total_count": totalCount,
                    "current_total": currentCount,
                }
            }
        )
    # except SQLAlchemyError as e:
    #     print("Database error:", e)
    #     abort(500, description="An internal server error occurred")
    # except (ProgrammingError, OperationalError) as e:
    #     print("Error while querying dataset:", e)
    #     abort(500, description="An error occurred while querying the dataset")
    except Exception as e:
        abort(500, description=f"Exception Occurred {str(e)}")