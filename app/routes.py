import os
current_path = os.getcwd()
from flask import Blueprint, render_template
bp = Blueprint('bp', '__name__', template_folder='frontend', static_folder='frontend/dashbrd/assets')
from .models import Products


@bp.route('/', methods=['GET'])
def index():
    return render_template('dashbrd/index.html')

@bp.route('/jobs', methods=['GET'])
def jobs():
    return render_template('dashbrd/job/jobs.html')

@bp.route('/job/running', methods=['GET'])
def jobsList():
    return render_template('dashbrd/job/joblist.html')

@bp.route('/job/new', methods=['GET'])
def jobsNew():
    return render_template('dashbrd/job/jobnew.html')