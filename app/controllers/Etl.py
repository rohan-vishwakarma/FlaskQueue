from flask import Flask, request
from flask_restful import Resource
from marshmallow import ValidationError
from app.schema.JobSchema import JobSchema

from pyspark.sql import SparkSession
import os

job_schema = JobSchema()

class Extract(Resource):
    def post(self):
        try:
            # Validate input using Marshmallow schema
            data = job_schema.load({
                "jobname": request.form.get("jobname"),
                "csvfile": request.files.get("csvfile")
            })

            # Extract validated data
            jobname = data["jobname"]
            csv_file = data["csvfile"]

            tmp_dir = "/tmp/uploads"
            os.makedirs(tmp_dir, exist_ok=True)
            csv_path = os.path.join(tmp_dir, csv_file.filename)
            csv_file.save(csv_path)

            # Create PySpark session
            spark = SparkSession.builder.master("local[*]").appName("Spark").getOrCreate()

            # Process CSV file using Spark (example)
            try:
                df = spark.read.csv(csv_path, header=True, inferSchema=True)
                row_count = df.count()
                print("row", row_count)
            finally:
                spark.stop()  # Ensure Spark session is stopped

            job = {
                "jobname": jobname,
                "csv_filename": csv_file.filename,
                "row_count": row_count
            }

            return {"message": "Job created successfully!", "job": job}, 201

        except ValidationError as err:
            return {"errors": err.messages}, 400

        except Exception as ex:
            return {"errors": str(ex)}, 500
