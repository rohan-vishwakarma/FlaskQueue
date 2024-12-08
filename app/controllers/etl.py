from flask import Flask, request
from flask_restful import Resource
from marshmallow import ValidationError
from app.schema.JobSchema import JobSchema
import os
from app.models import db, CeleryTask, Dataset

job_schema = JobSchema()


class Extract(Resource):
    def post(self):
        try:
            from app.celerytask.tasks import processCsvFile, hello
            data = job_schema.load({
                "datasetname": request.form.get("datasetname"),
                "csvfile": request.files.get("csvfile")
            })
            datasetName = data["datasetname"]
            csvFile = data["csvfile"]
            filepath = os.path.join('uploads', csvFile.filename)
            os.makedirs('uploads', exist_ok=True)
            csvFile.save(filepath)
            processCsvFile.delay(filepath, datasetName)

            return {"message": "Job created successfully!", "response" : "s"}, 201

        except ValidationError as err:
            return {"errors": err.messages}, 400

        except Exception as ex:
            return {"errors": str(ex)}, 500


    def get(self):
        try:
            tasks = db.session.query(CeleryTask).join(Dataset).order_by(CeleryTask.created_at.desc(),
                                                                        Dataset.created_at.desc()).all()
            tasks_data = [task.to_dict() for task in tasks]

            return {"status": True, "data": tasks_data}, 200


        except ValidationError as err:
            return {"errors": err.messages}, 400

        except Exception as ex:
            return {"errors": str(ex)}, 500
