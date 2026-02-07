from enum import Enum
import csv


class Mode(Enum):
    csv = 1

class Table(Enum):
    programs = 1
    applications = 2
    applicants = 3

class Importer:
    def __init__(self, db, table, mode):
        self.db = db
        self.table = table
        self.mode = mode


    def import_db(self, file):
        match self.mode:
            case Mode.csv:
                reader = csv.reader(open(file, 'r', encoding='utf-8'))
            
        if self.mode == Mode.csv:
            data = list(reader)
            print(data)
            match self.table:
                case Table.programs:
                    self.db.add_programs(data)
                case Table.applications:
                    self.db.add_application(data)
                case Table.applicants:
                    self.db.add_applicant(data)