from enum import Enum
import csv


class Mode(Enum):
    csv = 1

class Table(Enum):
    programs = 1
    applications = 2
    applicants = 3

class Importer:
    def __init__(self, file, db, table, mode):
        self.db = db
        self.table = table
        self.mode = mode
        match mode:
            case Mode.csv:
                self.reader = csv.reader(open(file, 'r', encoding='utf-8'))

    def import_db(self):
        if self.mode == Mode.csv:
            data = list(self.reader)
            print(data)
            match self.table:
                case Table.programs:
                    self.db.add_programs(data)
                case Table.applications:
                    self.db.add_application(data)
                case Table.applicants:
                    self.db.add_applicant(data)