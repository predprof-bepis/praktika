from flask import render_template, request
import logic


def add_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def mainPage():
        if request.method == "POST":
            selected_date = request.form.get('date')
            selected_program = request.form.get('program')

            scores = logic.get_scores(selected_date)
            places = logic.get_places_counts(selected_date)
            data = logic.get_data(selected_date, selected_program)
        else:
            selected_date="Нет дат"
            selected_program = "pm"
            scores = ""
            places = {
                "pm": "Нет данных",
                "ivt": "Нет данных",
                "itss": "Нет данных",
                "ib": "Нет данных"
            }
            data = {"pm": ("Нет данных", "Нет данных", "Нет данных")}

        dates = logic.get_dates()

        return render_template('index.html', 
                                dates=dates, 
                                scores=scores, 
                                date=selected_date, 
                                program=selected_program,
                                places=places,
                                data=data)
    
    @app.route('/download-pdf', methods=['GET'])
    def downloadPdfPage():
        return render_template('download-pdf.html')
    
    @app.route('/upload-db', methods=['GET', 'POST'])
    def uploadDbPage():
        return render_template('upload-db.html')
