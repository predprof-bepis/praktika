import sys
import os
import dbtools
from dbtools import import_db
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QDateEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate

db = dbtools.DB()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #окошко окошко
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
            self.table.setItem(i - 1, 1, QTableWidgetItem(fio))
            self.table.setItem(i - 1, 2, QTableWidgetItem(str(score)))
            self.table.setItem(i - 1, 3, QTableWidgetItem(str(priority)))
            self.table.setItem(i - 1, 4, QTableWidgetItem(str(consent)))
        self.result_label.setText(f"ОП: {selected_op}\nДата: {selected_date}\nЗаявлений: {len(rows_data)}")
#табличка
    def load_test_data(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбор CSV файлов", "", "CSV (*.csv);;Все файлы (*)"
        )
        if files:
            importer = import_db.Importer(db, import_db.Table.applications, import_db.Mode.csv)
            for i in files:
                importer.import_db(i)
            self._fill_programs_combo()
            self.result_label.setText(f"Добавлено файлов: {len(files)}\nСписок абитуриентов обновлён.")
        base = os.path.dirname(os.path.abspath(__file__))
        programs_path = os.path.join(base, "programs.csv")
        if os.path.isfile(programs_path):
            imp = import_db.Importer(db, import_db.Table.programs, import_db.Mode.csv)
            imp.import_db(programs_path)
        applications_path = os.path.join(base, "applications.csv")
        if os.path.isfile(applications_path):
            import_db.import_applications_fio(db, applications_path)
        self._fill_programs_combo()
        if self.op_combo.count() > 0:
            self.op_combo.setCurrentIndex(0)
            self.date_edit.setDate(QDate(2025, 2, 7))
            self.on_apply()
        else:
            self.table.setRowCount(0)
            self.result_label.setText("Пробные данные загружены из CSV.")

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
            importer = import_db.Importer(db, import_db.Table.programs, import_db.Mode.csv)
            for i in files:
                importer.import_db(i)
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
