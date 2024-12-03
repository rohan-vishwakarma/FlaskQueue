import io
import csv
from marshmallow import Schema, fields, ValidationError, validates

class JobSchema(Schema):
    jobname = fields.String(
        required=True,
        validate=lambda n: len(n) > 3,
        error_messages={"required": "Jobname is required.", "invalid": "Jobname must be longer than 3 characters."}
    )
    csvfile = fields.Raw(required=True, error_messages={"required": "A CSV file is required."})

    @validates("csvfile")
    def validate_csv(self, file):
        if not file.filename.endswith('.csv'):
            raise ValidationError("The uploaded file must be a CSV.")
        # Check if the file content is readable and valid CSV
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            file.stream.seek(0)  # Reset the stream for further processing
            csv.reader(stream)
        except Exception:
            raise ValidationError("The file is not a valid CSV format.")
