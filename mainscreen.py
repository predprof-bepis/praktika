import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QDateEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import QDate, Qt
from dbtools import DB


class DateSelector(QWidget):
    def __init__(self):
        super().__init__()

        # === КЛАСТЕР ПЕРЕМЕННЫХ ===
        self.window_title = "Выбор даты и ОП + фильтрация абитуриентов"
        self.window_width = 1000
        self.window_height = 800
        self.date_format = "dd.MM.yyyy"

        self.selected_program_id = None
        self.selected_program_name = ""

        # === ИНИЦИАЛИЗАЦИЯ БД ===
        self.db = DB(filename="database.db", autosave=True)

        # === ИНИЦИАЛИЗАЦИЯ ВИДЖЕТОВ ===
        self.setWindowTitle(self.window_title)
        self.resize(self.window_width, self.window_height)

        layout = QVBoxLayout()

        # Виджет выбора даты
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        # Метки
        self.label_date = QLabel(f"Выбранная дата: {self.date_edit.date().toString(self.date_format)}")
        self.label_program = QLabel("Выбранная ОП: не выбрана")

        # Таблица программ
        self.table_programs = QTableWidget()
        self.load_programs_into_table()

        # Таблица абитуриентов (изначально пустая)
        self.table_applicants = QTableWidget()
        self.table_applicants.setHorizontalHeaderLabels([
            "ID", "Физика/ИКТ", "Русский", "Математика", "ИД", "Балл"
        ])
        self.table_applicants.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Подключение сигналов
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.table_programs.cellClicked.connect(self.on_program_selected)

        # Добавление в макет
        layout.addWidget(self.date_edit)
        layout.addWidget(self.label_date)
        layout.addWidget(self.label_program)
        layout.addWidget(QLabel("Образовательные программы:"))
        layout.addWidget(self.table_programs)
        layout.addWidget(QLabel("Абитуриенты, подавшие на выбранную ОП:"))
        layout.addWidget(self.table_applicants)

        self.setLayout(layout)

    def load_programs_into_table(self):
        """Загружает программы из БД."""
        programs = self.db.get_program()

        self.table_programs.setRowCount(len(programs))
        self.table_programs.setColumnCount(3)
        self.table_programs.setHorizontalHeaderLabels(["ID", "Название", "Бюджетные места"])

        for row_idx, row_data in enumerate(programs):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_programs.setItem(row_idx, col_idx, item)

        self.table_programs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def on_date_changed(self, date):
        self.label_date.setText(f"Выбранная дата: {date.toString(self.date_format)}")

    def on_program_selected(self, row, column):
        """Обрабатывает выбор ОП и загружает связанных абитуриентов."""
        program_id = int(self.table_programs.item(row, 0).text())
        program_name = self.table_programs.item(row, 1).text()

        self.selected_program_id = program_id
        self.selected_program_name = program_name
        self.label_program.setText(f"Выбранная ОП: {program_name} (ID: {program_id})")

        # Загрузка абитуриентов, подавших на эту программу
        self.load_applicants_for_program(program_id)

    def load_applicants_for_program(self, program_id):
        """Загружает абитуриентов, связанных с program_id через таблицу applications."""
        # SQL-запрос: соединяем applicants и applications
        query = """
        SELECT a.id, a.physics_or_ict, a.russian, a.math, 
               a.individual_achievements, a.total_score
        FROM applicants a
        JOIN applications app ON a.id = app.applicant_id
        WHERE app.program_id = ?
        ORDER BY a.total_score DESC
        """
        # Выполняем запрос через ваш метод run (он принимает *args)
        rows = self.db.run(query, program_id)

        # Обновляем таблицу
        self.table_applicants.setRowCount(len(rows))
        self.table_applicants.setColumnCount(6)

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_applicants.setItem(row_idx, col_idx, item)

        self.table_applicants.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DateSelector()
    window.show()
    sys.exit(app.exec())