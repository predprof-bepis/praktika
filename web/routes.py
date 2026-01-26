from flask import render_template

def add_routes(app):
    @app.route('/', methods=['GET'])
    def mainPage():
        return render_template('index.html')
    
    @app.route('/download-pdf', methods=['GET'])
    def downloadPdfPage():
        return render_template('download-pdf.html')