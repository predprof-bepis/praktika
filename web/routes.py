from flask import render_template

def add_routes(app):
    @app.route('/', methods=['GET'])
    def mainPage():
        return render_template('index.html')