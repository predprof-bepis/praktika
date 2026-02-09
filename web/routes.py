from flask import render_template, request, send_file, flash
import logic
import pdfgenerator
import os
from werkzeug.utils import secure_filename
from dbtools.import_db import Importer, Mode, Table


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
        if request.method == 'POST':
            if 'csv_file' not in request.files:
                return render_template('upload-db.html', 
                                    message='Файл не выбран', 
                                    success=False)
            
            file = request.files['csv_file']
            table_type = request.form.get('table_type')
            
            if file.filename == '':
                return render_template('upload-db.html', 
                                    message='Файл не выбран', 
                                    success=False)
            
            if not file.filename.endswith('.csv'):
                return render_template('upload-db.html', 
                                    message='Поддерживаются только CSV файлы', 
                                    success=False)

            upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            try:
                table_map = {
                    'programs': Table.programs,
                    'applicants': Table.applicants,
                    'applications': Table.applications
                }
                
                if table_type not in table_map:
                    return render_template('upload-db.html', 
                                        message='Неверный тип таблицы', 
                                        success=False)

                match table_type:
                    case "programs":
                        logic.db_manager.db.run("DELETE FROM programs")
                    case "applicants":
                        logic.db_manager.db.run("DELETE FROM applicants")
                    case "applications":
                        logic.db_manager.db.run("DELETE FROM applications")


                importer = Importer(logic.db_manager.db, table_map[table_type], Mode.csv)
                importer.import_db(filepath)

                os.remove(filepath)
                
                return render_template('upload-db.html', 
                                    message=f'Данные успешно импортированы в таблицу {table_type}', 
                                    success=True)
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return render_template('upload-db.html', 
                                    message=f'Ошибка при импорте: {str(e)}', 
                                    success=False)
        
        return render_template('upload-db.html')
