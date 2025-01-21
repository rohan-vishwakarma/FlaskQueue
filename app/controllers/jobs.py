from itertools import count
from math import trunc

from flask import request, abort, render_template
from flask_restful import Resource, reqparse
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError, SQLAlchemyError

from app.models import Dataset, db
from app.schema.JobSchema import  DownloadFileSchema, ValidateUuid

import os

uploadFolder = os.path.abspath("uploads")
os.makedirs(uploadFolder, exist_ok=True)

class Jobs(Resource):
    def __init__(self):
        self.schema = ValidateUuid()

    def get(self):
        try:
            params = request.args
            limit = 10 if not params.get('limit', 10) else int(params.get('limit', 10))
            page  = 1  if not params.get('page', 1)  else int(params.get('page', 1))
            uuid  = params.get('uuid')

            if uuid is None:
                return  {"success": False, "message": "uuid is required"}, 400

            celeryTask = db.session.query(Dataset.task_id, Dataset.name).filter_by(task_id=uuid).first()
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
                return {"success": False, "message" : "No Records Found"}, 404

            return {
                "success": True,
                "message": "The Request Proceeded",
                "data": rowsAsDict,
                "columns": list(columns),
                "meta" : {
                    "limit" : limit,
                    "page" : page,
                    "total_count" : totalCount,
                    "current_total": currentCount
                }
            }, 200

        except SQLAlchemyError as e:
            print("Database error:", e)
            abort(500, description="An internal server error occurred")

        except (ProgrammingError, OperationalError) as e:
            print("Error while querying dataset:", e)
            abort(500, description="An error occurred while querying the dataset")

        except Exception as e:
            abort(500, description=f"Exception Occurred {str(e)}")



