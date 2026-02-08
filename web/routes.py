from flask import render_template

def add_routes(app):
    @app.route('/', methods=['GET'])
    def mainPage():
        return render_template('index.html')
    
    @app.route('/download-pdf', methods=['GET'])
    def downloadPdfPage():
        return render_template('download-pdf.html')
    
    @app.route('/upload-db', methods=['GET', 'POST'])
    def uploadDbPage():
        return render_template('upload-db.html')
