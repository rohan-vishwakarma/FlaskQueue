import os
from dotenv import load_dotenv
load_dotenv()

APIBASEURL = os.getenv('APIBASEURL')

jobs = APIBASEURL + '/etl/extract'