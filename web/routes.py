from flask import render_template, request
import logic


def add_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def mainPage():
        if request.method == "POST":
            selected_date = request.form.get('date')
            scores = logic.get_scores(selected_date)
            places = logic.get_places_counts(selected_date)
        else:
            selected_date="Нет дат"
            scores = ""
            places = {
                "pm": "Нет данных",
                "ivt": "Нет данных",
                "itss": "Нет данных",
                "ib": "Нет данных"
            }

        dates = logic.get_dates()

        return render_template('index.html', dates=dates, scores=scores, date=selected_date, places=places)
    
    @app.route('/download-pdf', methods=['GET'])
    def downloadPdfPage():
        return render_template('download-pdf.html')
    
    @app.route('/upload-db', methods=['GET', 'POST'])
    def uploadDbPage():
        return render_template('upload-db.html')
