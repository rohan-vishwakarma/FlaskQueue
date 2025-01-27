import sys
from pathlib import Path
import datetime
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.celery_app import celery_app
from app import create_app
from app.utils.etl_utilities import DatasetService
from app.models import db, Dataset, CeleryTask
app = create_app()

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


@celery_app.task(bind=True)
def processCsvFile(self, file_content, datasetName):
    startedAt = datetime.datetime.now()
    print(f" {datasetName} is Processing ")
    tid = self.request.id
    with app.app_context():
        spark = None
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.master("local[*]").appName("CSVProcessor").getOrCreate()
            self.update_state(state='PROGRESS', meta={'progress': "IN Progress"})
            Session = sessionmaker(bind=db.engine)
            df = spark.read.csv(file_content, header=True, inferSchema=True)
            totalRows = df.count()
            df.show()

            dataService = DatasetService()
            tableName = dataService.createTable(datasetName)
            tableQuery = dataService.generateCreateTableQuery(df, tableName)
            Dataset.insert(tableName, self.request.id)
            db.session.execute(text(tableQuery))
            db.session.commit()

            updateSession = Session()
            update = updateSession.query(Dataset).filter_by(task_id=str(tid)).first()
            if update:
                update.total_rows = totalRows
                updateSession.commit()

            columns = [col.replace(' ', '_').replace('-', '_').replace(':', '_') + "_" for col in df.columns]
            column_names = ', '.join(columns)
            print("column names" + column_names)
            progressInterval = totalRows // 5
            rowProcessed = 0

            progressUpdatePoints = [totalRows * i // 5 for i in range(1, 6)]
            nextUpdatePoint = progressUpdatePoints.pop(0)

            for row in df.collect():
                values_placeholders = ', '.join([':{}'.format(col) for col in columns])
                insert_query = text(f"INSERT INTO {tableName} ({column_names}) VALUES ({values_placeholders})")
                params = {columns[i]: row[i] for i in range(len(columns))}
                db.session.execute(insert_query, params)
                rowProcessed += 1
                progressSession = Session()
                if rowProcessed >= nextUpdatePoint:
                    progress = int((rowProcessed / totalRows) * 100)
                    self.update_state(state='PROGRESS', meta={'progress': f"{progress}%"})
                    taskId = self.request.id
                    updateProgress = progressSession.query(CeleryTask).filter_by(task_id=taskId).first()
                    updateProgress.progress = progress
                    progressSession.commit()
                    print(f"Progress: {progress}%")
                    if progressUpdatePoints:
                        nextUpdatePoint = progressUpdatePoints.pop(0)

            finishedAt = datetime.datetime.now()
            updateTime = db.session.query(Dataset).filter_by(task_id=tid).first()
            updateTime.finished_at = finishedAt
            updateTime.started_at = startedAt

            db.session.commit()

            print(f"Data successfully inserted into {tableName}")

        except Exception as e:
            print(f"Error processing CSV file: {tid} {e}")  # Replace tid with taskId
            db.session.rollback()

            try:
                exceptionSession = Session()
                update = exceptionSession.query(CeleryTask).filter_by(task_id=str(tid)).first()
                if update:
                    update.status = "FAILURE"
                    exceptionSession.commit()  # Commit the failure status update
                    print(f"Task ID {tid} status updated to FAILURE.")
                else:
                    print(f"No record found for task ID: {tid}")
            except Exception as db_error:
                print(f"Error updating task status for task ID {tid}: {db_error}")
        finally:
            if spark:
                spark.stop()




@celery_app.task
def hello():
    print("this is a task")
