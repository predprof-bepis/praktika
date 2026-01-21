from flask import render_template
from app import app


@app.route('/', methods=['GET'])
def mainPage():
    return render_template('index.html')