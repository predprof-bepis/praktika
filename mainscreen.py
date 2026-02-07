import sys
import os
import dbtools
from dbtools.import_db import Importer, Table, Mode
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QDateEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate
import csv

db = dbtools.DB()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # окошко окошко
        self.setWindowTitle("Выбор ОП и даты")
        self.setGeometry(300, 300, 600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        title_label = QLabel("Выберите ОП и дату:")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        op_layout = QHBoxLayout()
        op_label = QLabel("ОП:")
        self.op_combo = QComboBox()
        self._fill_programs_combo()
        op_layout.addWidget(op_label)
        op_layout.addWidget(self.op_combo)
        layout.addLayout(op_layout)
        date_layout = QHBoxLayout()
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        self.apply_button = QPushButton("Применить")
        self.apply_button.clicked.connect(self.on_apply)
        layout.addWidget(self.apply_button)

        self.dataset_button = QPushButton("Добавить данные ОПа а у меня тоже есть птички")
        self.dataset_button.clicked.connect(self.dataset)
        layout.addWidget(self.dataset_button)

        self.clear_op_button = QPushButton("Очистить ОП в БД")
        self.clear_op_button.clicked.connect(self.clear_programs_confirm)
        layout.addWidget(self.clear_op_button)

        self.load_test_button = QPushButton("Загрузить данные")
        self.load_test_button.clicked.connect(self.load_test_data)
        layout.addWidget(self.load_test_button)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["№", "ID", "Балл", "Приоритет", "Согласие"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def _norm_date(self, s):
        parts = str(s).strip().split(".")
        if len(parts) != 3:
            return str(s).strip()
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{d:02d}.{m:02d}.{y:04d}"
        except (ValueError, TypeError):
            return str(s).strip()

    def on_apply(self):
        selected_op = self.op_combo.currentText()
        selected_date = self._norm_date(self.date_edit.date().toString("dd.MM.yyyy"))

        if "Выберите" in selected_op or not selected_op:
            QMessageBox.warning(self, "Ошибка", "Выберите ОП")
            return

        programs = db.get_program()
        program_id = None
        for row in programs:
            if row[1] == selected_op:
                program_id = row[0]
                break
        if program_id is None:
            self.result_label.setText("ОП не найден в БД")
            self.table.setRowCount(0)
            return

        applications = db.get_application()
        apps_for_op_date = [a for a in applications if a[2] == program_id and self._norm_date(a[3]) == selected_date]
        rows_data = []
        for app in apps_for_op_date:
            applicant_id = app[1]
            priority = app[4]
            consent = app[5]
            applicant_rows = db.get_applicant(applicant_id)
            if applicant_rows:
                r = applicant_rows[0]
                total_score = r[5]
                fio = r[6] if len(r) > 6 else ""
            else:
                total_score = 0
                fio = ""
            rows_data.append((fio, total_score, priority, consent))
        rows_data.sort(key=lambda x: x[1], reverse=True)

        self.table.setRowCount(len(rows_data))
        for i, (fio, score, priority, consent) in enumerate(rows_data, 1):
            self.table.setItem(i - 1, 0, QTableWidgetItem(str(i)))
            self.table.setItem(i - 1, 1, QTableWidgetItem(str(fio)))
            self.table.setItem(i - 1, 2, QTableWidgetItem(str(score)))
            self.table.setItem(i - 1, 3, QTableWidgetItem(str(priority)))
            self.table.setItem(i - 1, 4, QTableWidgetItem(str(consent)))
        self.result_label.setText(f"ОП: {selected_op}\nДата: {selected_date}\nЗаявлений: {len(rows_data)}")

    # табличка
    def load_test_data(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбор CSV файлов", "", "CSV (*.csv);;Все файлы (*)"
        )
        if files:
            for file_path in files:
                # Проверяем, является ли файл специфическим форматом с именами ОП
                if self.is_custom_applications_format(file_path):
                    self.import_custom_applications(file_path)
                else:
                    # Определяем тип файла по его имени
                    filename_lower = os.path.basename(file_path).lower()

                    if any(keyword in filename_lower for keyword in ['application', 'app', 'заявлени']):
                        importer = Importer(db, Table.applications, Mode.csv)
                    elif any(keyword in filename_lower for keyword in ['program', 'prog', 'оп', 'sp']):
                        importer = Importer(db, Table.programs, Mode.csv)
                    elif any(keyword in filename_lower for keyword in ['applicant', 'abitur', 'person']):
                        importer = Importer(db, Table.applicants, Mode.csv)
                    else:
                        # Если не можем определить автоматически, спрашиваем пользователя
                        reply = QMessageBox.question(
                            self,
                            "Тип данных",
                            f"Какие данные содержатся в файле {os.path.basename(file_path)}?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                            QMessageBox.Yes
                        )

                        if reply == QMessageBox.Yes:  # Заявления
                            importer = Importer(db, Table.applications, Mode.csv)
                        elif reply == QMessageBox.No:  # Программы
                            importer = Importer(db, Table.programs, Mode.csv)
                        else:  # Отмена или Абитуриенты (по умолчанию)
                            continue

                    importer.import_db(file_path)

            self._fill_programs_combo()
            self.result_label.setText(f"Добавлено файлов: {len(files)}\nСписок абитуриентов обновлён.")

        base = os.path.dirname(os.path.abspath(__file__))
        programs_path = os.path.join(base, "programs.csv")
        if os.path.isfile(programs_path):
            imp = Importer(db, Table.programs, Mode.csv)
            imp.import_db(programs_path)
        applications_path = os.path.join(base, "applications.csv")
        if os.path.isfile(applications_path):
            # Проверяем, является ли файл специфическим форматом с именами ОП
            if self.is_custom_applications_format(applications_path):
                self.import_custom_applications(applications_path)
            else:
                importer = Importer(db, Table.applications, Mode.csv)
                importer.import_db(applications_path)
        self._fill_programs_combo()
        if self.op_combo.count() > 0:
            self.op_combo.setCurrentIndex(0)
            self.date_edit.setDate(QDate(2025, 2, 7))
            self.on_apply()
        else:
            self.table.setRowCount(0)
            self.result_label.setText("Пробные данные загружены из CSV.")

    def is_custom_applications_format(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('id,баллы,дата,ОП'):
                    return True
            return False
        except:
            return False

    def import_custom_applications(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            print(f"Файл {file_path} не найден.")
            return
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            except UnicodeDecodeError:
                print(f"Не удалось декодировать файл {file_path} ни с utf-8, ни с cp1251.")
                return

        if not rows:
            print("Файл пустой.")
            return

        # Получаем текущие программы из БД для сопоставления имени с ID
        programs_list = db.get_program()
        program_name_to_id = {row[1]: row[0] for row in programs_list}  # {name: id}

        # Подготовим списки для вставки
        applicants_to_add = []  # (physics_or_ict, russian, math, individual_achievements, total_score)
        applications_to_add = []  # (applicant_id, program_id, date, priority, consent)

        for row in rows:
            try:
                # Обработка даты: DD.MM.YYYY -> YYYY-MM-DD
                date_parts = row['дата'].split('.')
                if len(date_parts) != 3:
                    print(f"Неверный формат даты '{row['дата']}' для строки {row}. Пропуск.")
                    continue
                day, month, year = date_parts
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                # Сопоставление ОП с program_id
                op_name = row['ОП']
                program_id = program_name_to_id.get(op_name)
                if program_id is None:
                    print(f"ОП '{op_name}' не найдена в БД. Пропуск строки {row}.")
                    continue

                # Общий балл
                total_score = int(row['баллы'])

                # Генерация условных баллов для физики/русского/математики
                avg_subject_score = total_score // 3
                physics_or_ict = avg_subject_score
                russian = avg_subject_score
                math = total_score - physics_or_ict - russian
                individual_achievements = 0

                # Добавляем в список абитуриентов
                applicant_id = int(row['id'])  # Используем id из CSV как ID абитуриента
                applicants_to_add.append(
                    (physics_or_ict, russian, math, individual_achievements, total_score, applicant_id))

            except (ValueError, KeyError) as e:
                print(f"Ошибка при обработке строки {row}: {e}. Пропуск.")
                continue

        # --- Добавление абитуриентов ---
        if applicants_to_add:
            print(f"Добавляем {len(applicants_to_add)} абитуриентов...")
            # Вставляем с указанием applicant_id напрямую
            for app_data_with_id in applicants_to_add:
                physics_or_ict, russian, math, individual_achievements, total_score, applicant_id = app_data_with_id
                # Проверим, существует ли уже абитуриент с таким ID
                existing_applicant = db.run("SELECT id FROM applicants WHERE id = ?", applicant_id)
                if existing_applicant:
                    print(f"Абитуриент с ID {applicant_id} уже существует. Пропуск.")
                    continue

                # Вставляем с указанием ID, используя обычный run
                db.run(
                    "INSERT OR IGNORE INTO applicants (id, physics_or_ict, russian, math, individual_achievements, total_score) VALUES (?, ?, ?, ?, ?, ?)",
                    applicant_id, physics_or_ict, russian, math, individual_achievements, total_score)
            print(f"Успешно обработаны абитуриенты.")

            # --- Добавляем заявления ---
            for row in rows:
                try:
                    # Повторяем проверки
                    date_parts = row['дата'].split('.')
                    if len(date_parts) != 3: continue
                    day, month, year = date_parts
                    formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    op_name = row['ОП']
                    if op_name not in program_name_to_id: continue

                    applicant_id = int(row['id'])
                    program_id = program_name_to_id[op_name]
                    priority = 1  # или другое значение по умолчанию
                    consent = 0  # или другое значение по умолчанию
                    applications_to_add.append((applicant_id, program_id, formatted_date, priority, consent))
                except (ValueError, KeyError) as e:
                    print(f"Ошибка при формировании заявления для строки {row}: {e}. Пропуск.")
                    continue

            if applications_to_add:
                print(f"Добавляем {len(applications_to_add)} заявлений...")
                # Удалим дубликаты, если они есть (по applicant_id, program_id, date)
                unique_apps = []
                seen_keys = set()
                for app in applications_to_add:
                    key = (app[0], app[1], app[2])  # applicant_id, program_id, date
                    if key not in seen_keys:
                        unique_apps.append(app)
                        seen_keys.add(key)

                if unique_apps:
                    db.run_many(
                        "INSERT OR IGNORE INTO applications (applicant_id, program_id, date, priority, consent) VALUES (?, ?, ?, ?, ?)",
                        *unique_apps)
                    print(f"Успешно добавлено {len(unique_apps)} уникальных заявлений.")
                else:
                    print("Не осталось уникальных заявлений для добавления.")
            else:
                print("Не удалось сформировать ни одного заявления для добавления.")
        else:
            print("Не было абитуриентов для добавления.")

    def _fill_programs_combo(self):
        self.op_combo.clear()
        rows = db.get_program()
        names = [str(row[1]) for row in rows]
        self.op_combo.addItems(names)

    def dataset(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбор CSV файлов", "", "CSV (*.csv);;Все файлы (*)"
        )
        if files:
            importer = Importer(db, Table.programs, Mode.csv)
            for file_path in files:
                importer.import_db(file_path)
            self._fill_programs_combo()
            self.result_label.setText(f"Добавлено файлов: {len(files)}\nСписок ОП обновлён.")

    def clear_programs_confirm(self):
        r = QMessageBox.question(
            self, "Подтверждение",
            "Точно уверены? Все ОП будут удалены из базы данных.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if r == QMessageBox.Yes:
            db.run("DELETE FROM programs")
            self._fill_programs_combo()
            self.result_label.setText("Список ОП очищен.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())