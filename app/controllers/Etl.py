from flask import Flask, request
from flask_restful import Resource
from marshmallow import ValidationError
from app.schema.JobSchema import JobSchema

from pyspark.sql import SparkSession

job_schema = JobSchema()

class Extract(Resource):
    def post(self):
        try:
            data = job_schema.load({
                "jobname": request.form.get("jobname"),
                "csvfile": request.files.get("csvfile")
            })
            job = {
                "jobname": data["jobname"],
                "csv_filename": data["csvfile"].filename
            }
            return {"message": "Job created successfully!", "job": job}, 201

        except ValidationError as err:
            return {"errors": err.messages}, 400
        except Exception as ex:
            return  {"errors": ex}, 500
