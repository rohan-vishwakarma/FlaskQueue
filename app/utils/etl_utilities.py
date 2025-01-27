import os
from pyspark.sql import SparkSession
from datetime import date
from app.models import  Dataset

# Initialize Spark Session
class FileHandler:

    def __init__(self, tmp_dir="/tmp/uploads"):
        self.tmp_dir = tmp_dir
        os.makedirs(self.tmp_dir, exist_ok=True)

    def saveFile(self, file):
        """Saves the uploaded CSV file to the temporary directory."""
        filePath = os.path.join(self.tmp_dir, file.filename)
        file.save(filePath)
        return filePath

    def removeFile(self, filePath):
        """Removes the temporary CSV file."""
        if os.path.exists(filePath):
            os.remove(filePath)
            print(f"File {filePath} removed.")
        else:
            print(f"File {filePath} does not exist.")

class DataProcessor:

    def __init__(self, sparkSession):
        self.spark = sparkSession

    def loadData(self, csvPath):
        """Loads the CSV data into a Spark DataFrame."""
        return self.spark.read.csv(csvPath, header=True, inferSchema=True)

    def countRows(self, df):
        """Returns the number of rows in the DataFrame."""
        return df.count()

    def cleanColumnNames(self, df):
        """Replaces blank spaces in column names with underscores."""
        cleaned_columns = [col.replace(" ", "_") for col in df.columns]
        df = df.toDF(*cleaned_columns)  # Renaming columns
        return df


class DatasetService:
    """Manages the complete dataset processing flow."""
    def __init__(self):
        self.fileHandler = FileHandler()
        sparkSession = SparkSession.builder.master("local[*]").appName("Spark").getOrCreate()
        self.dataProcessor = DataProcessor(sparkSession)

    def getSqlType(self, spark_type):
        """Maps Spark DataFrame types to SQL types."""
        type_mapping = {
            "StringType": "TEXT",
            "IntegerType": "INT",
            "LongType": "BIGINT",
            "DoubleType": "DOUBLE",
            "FloatType": "FLOAT",
            "BooleanType": "BOOLEAN",
            "DateType": "DATE",
            "TimestampType": "DATETIME",
            "DecimalType": "DECIMAL(10,2)",
            "ArrayType": "TEXT",  # SQL doesn't have an array type, use TEXT for simplicity
            "MapType": "TEXT",  # Map also represented as TEXT for simplicity
        }

        return type_mapping.get(spark_type, "TEXT")

    def generateCreateTableQuery(self, df, table_name):
        """Generates SQL CREATE TABLE query from DataFrame schema."""
        columns = df.schema.fields
        column_defs = ["dataset_id INT(20) PRIMARY KEY NOT NULL AUTO_INCREMENT"]

        for col in columns:
            col_name = col.name
            col_type = self.getSqlType(str(col.dataType))

            # Clean the column name to be SQL-friendly
            cleaned_col_name = col_name.replace(" ", "_").replace('-', '_').replace(':', '_').lower()

            column_defs.append(f"{cleaned_col_name}{"_"} {col_type}")

        # Create the SQL query string
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        create_table_query += ",\n".join(column_defs)
        create_table_query += "\n);"

        return create_table_query

    def createTable(self, jobName):
        srNo = Dataset.count()
        currentDate = date.today()
        currentDate = str(currentDate)
        currentDate = currentDate.replace('-', '_')
        tableName = "DATASET_" + str(srNo) + "_" + str(jobName)
        tableName = tableName.replace(" ", "_").strip()
        tableName = tableName + "_" + str(currentDate)
        tableName = tableName.upper()
        return tableName

    def createDatasetTable(self, csvFile, jobName):
        """Orchestrates the flow of saving the file, loading data, and counting rows."""
        filePath = None
        try:
            filePath = self.fileHandler.saveFile(csvFile)
            df = self.dataProcessor.loadData(filePath)
            df = self.dataProcessor.cleanColumnNames(df)

            print(f"Cleaned DataFrame schema: {df.schema}")
            tableName = self.createTable(jobName)
            create_table_query = self.generateCreateTableQuery(df, tableName)

            return create_table_query
        except Exception as e:
            print(f"Error occurressd: {e}")
        finally:
            # Clean up by removing the file
            self.fileHandler.removeFile(filePath)


