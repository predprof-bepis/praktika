from flask import render_template, request, send_file
import logic
import pdfgenerator


def add_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def mainPage():
        if request.method == "POST":
            selected_date = request.form.get('date')
            selected_program = request.form.get('program')
            print(f"date: {selected_date}, program: {selected_program}")
            if selected_program == None:
                selected_program = "pm"

            scores = logic.get_scores(selected_date)
            places = logic.get_places_counts(selected_date)
            
            data = logic.get_data(selected_date, [selected_program])
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
            data = {"pm": [("1", "2", "3")]}

        dates = logic.get_dates()
        print(f"date: {selected_date}, program: {selected_program}, data: {data}")

        return render_template('index.html', 
                                dates=dates, 
                                scores=scores, 
                                date=selected_date, 
                                program=selected_program,
                                places=places,
                                data=data)
    
    @app.route('/download-pdf', methods=['GET', 'POST'])
    def downloadPdfPage():
        match request.method:
            case "POST":
                print(request.form.get("date"))
                a = pdfgenerator.PDFGenerator(logic.db_manager.db, logic.db_manager)
                a.generate_pdf("resultador.pdf", request.form.get("date"))
                return send_file('resultador.pdf')
            case "GET":
                return render_template('download-pdf.html', dates=logic.get_dates())
    
    @app.route('/upload-db', methods=['GET', 'POST'])
    def uploadDbPage():
        return render_template('upload-db.html')
