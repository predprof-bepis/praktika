import traceback
from enum import Enum
import csv
from datetime import datetime


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
        if self.mode != Mode.csv:
            return
        with open(file, 'r', encoding='utf-8') as f:
            data = list(csv.reader(f))
        if not data:
            return
        if self.table == Table.programs:
            data = data[1:] if _is_header(data[0]) else data
            self.db.add_programs(_rows_programs(data))
        elif self.table == Table.applications:
            data = data[1:] if _is_header(data[0]) else data
            self.db.add_application(_rows_application(data, self.db))
        elif self.table == Table.applicants:
            data = data[1:] if _is_header(data[0]) else data
            self.db.add_applicant(_rows_applicant(data))


def _is_header(row: list[str]):
    flag = True
    for i in row:
        if i.isdecimal():
            flag = False
    # Вероятно, все данные в таблице будут иметь хотя бы одно число, если нет, это хедер
    return flag

def _rows_programs(rows):
    final = []
    for i in rows:
        # Зачем грузить битые данные?
        if len(i) == 2:
            if not i[1].isdecimal():
                continue

            final.append([i[0], int(i[1])])
        else:
            if not i[2].isdecimal() and i[0].isdecimal():
                continue

            final.append([int(i[0]), i[1], int(i[2])])

    return final

def _rows_application(rows, db):
    final = []
    for i in rows:
        if len(i) != 5 and len(i) != 6:
            continue

        if len(i) == 5:
            if not i[0].isdecimal() or\
                    not i[3].isdecimal() or\
                    not i[4].isdecimal():
                continue

            try:
                datetime.strptime(i[2], "%Y-%m-%d")
            except:
                continue

            final.append([
                          int(i[0]),
                          int(i[1]) if i[1].isdecimal() else db.run("SELECT id FROM programs WHERE name = ?", i[1])[0][0],
                          datetime.strptime(i[2], "%Y-%m-%d"),
                          int(i[3]),
                          int(i[4])
                          ])
        else:
            if not i[0].isdecimal() or \
                    i[1].isdecimal() or\
                    not i[4].isdecimal() or\
                    not i[5].isdecimal():
                continue

            try:
                datetime.strptime(i[2], "%Y-%m-%d")
            except:
                continue

            final.append([
                          int(i[0]),
                          int(i[1]),
                          int(i[2]) if i[2].isdec                          datetime.strptime(i[2], "%Y-%m-%d"),
                          int(i[3]),imal() else db.run("SELECT id FROM programs WHERE name = ?", i[2])[0][0],
                          datetime.strptime(i[3], "%Y-%m-%d"),
                          int(i[4]),
                          int(i[5])
                          ])
    return final


def _rows_applicant(rows):
    final = []
    for row in rows:
        if len(row) != 5:
            try:
                return [int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])]
            except (ValueError, TypeError):
                continue
        elif len(row) == 4:
            try:
                return [int(row[0]), int(row[1]), int(row[2]), int(row[3]), sum([int(row[0]), int(row[1]), int(row[2]), int(row[3])])]
            except (ValueError, TypeError):
                continue
    return final
