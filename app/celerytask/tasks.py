import sys
from pathlib import Path

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
    with app.app_context():
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.master("local[*]").appName("CSVProcessor").getOrCreate()
            self.update_state(state='PROGRESS', meta={'progress': "IN PRogress"})

            # Load CSV into a PySpark DataFrame
            df = spark.read.csv(file_content, header=True, inferSchema=True)
            totalRows = df.count()
            df.show()  # For debugging: Show the content of the DataFrame

            # Create the table dynamically
            dataService = DatasetService()
            tableName = dataService.createTable(datasetName)
            tableQuery = dataService.generateCreateTableQuery(df, tableName)
            Dataset.insert(tableName, self.request.id)
            db.session.execute(text(tableQuery))
            db.session.commit()

            columns = df.columns
            column_names = ', '.join(columns)
            progressInterval = totalRows // 5
            rowProcessed = 0

            progressUpdatePoints = [totalRows * i // 5 for i in range(1, 6)]
            nextUpdatePoint = progressUpdatePoints.pop(0)

            for row in df.collect():
                values_placeholders = ', '.join([':{}'.format(col) for col in columns])
                insert_query = text(f"INSERT INTO {tableName} ({column_names}) VALUES ({values_placeholders})")
                # Map row data to parameters
                params = {columns[i]: row[i] for i in range(len(columns))}
                db.session.execute(insert_query, params)
                rowProcessed += 1

                Session = sessionmaker(bind=db.engine)
                progressSession = Session()
                # Update progress at the designated points
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

            db.session.commit()  # Commit the inserts
            print(f"Data successfully inserted into {tableName}")

        except Exception as e:
            print(f"Error processing CSV file: {e}")
            db.session.rollback()
        finally:
            spark.stop()


@celery_app.task
def hello():
    print("this is a task")
