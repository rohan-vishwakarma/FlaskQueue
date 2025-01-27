import os
from datetime import datetime
from marshmallow import ValidationError
from sqlalchemy import text
from app.utils.helper import human_readable_date

current_path = os.getcwd()
from flask import Blueprint, render_template, request, abort
bp = Blueprint('bp', '__name__', template_folder='frontend', static_folder='frontend/dashbrd/assets')
from .models import Products, db, CeleryTask, Dataset

@bp.route('/', methods=['GET', 'POST'])
def index():
    totalDatsetProcessed = db.session.query(Dataset).count()
    totalFailedTask = db.session.query(CeleryTask).filter_by(status='FAILURE').count()
    totalSuccessTask = db.session.query(CeleryTask).filter_by(status='SUCCESS').count()
    totalPendingTask = db.session.query(CeleryTask).filter_by(status='PENDING').count()

    query = db.session.query(Dataset).all()
    processingTimes = []
    for data in query:
        data = data.to_dict()
        started_at = datetime.strptime( str(data['started_at']), '%Y-%m-%d %H:%M:%S') if data['started_at'] is not None else None 
        finished_at = datetime.strptime(str(data['finished_at']), '%Y-%m-%d %H:%M:%S') if data['finished_at'] is not None else None 
        if started_at is not None and finished_at is not None:
            processingTime = (finished_at - started_at).total_seconds()
            processingTimes.append(processingTime)
    
    averageTime = sum(processingTimes) / len(processingTimes) if processingTimes else 0
    inMinutes = averageTime / 60

    data = {
        "totalDatasetProcessed": totalDatsetProcessed,
        "totalFailedTask": totalFailedTask,
        "totalSuccessTask": totalSuccessTask,
        "totalPendingTask": totalPendingTask,
        "average_processing_time_seconds": round(inMinutes, 2)
    }

    return render_template('dashbrd/index.html', data=data)


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

        tasks_data = []
        for task in tasks:
            task_dict = task.to_dict()
            task_dict["created_at"] = human_readable_date(task_dict["created_at"])
            tasks_data.append(task_dict)

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