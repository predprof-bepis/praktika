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
        if self.mode != Mode.csv:
            return
        with open(file, 'r', encoding='utf-8') as f:
            data = list(csv.reader(f))
        if not data:
            return
        if self.table == Table.programs:
            data = data[1:] if _is_header(data[0]) else data
            data = [_row_program(r) for r in data if len(r) >= 2]
            self.db.add_programs(data)
        elif self.table == Table.applications:
            data = data[1:] if _is_header(data[0]) else data
            data = [x for r in data if len(r) >= 5 and (x := _row_application(r)) is not None]
            self.db.add_application(data)
        elif self.table == Table.applicants:
            data = data[1:] if _is_header(data[0]) else data
            data = [x for r in data if len(r) >= 5 and (x := _row_applicant(r)) is not None]
            data = [[''] + x for x in data]
            self.db.add_applicant(data)


def _is_header(row):
    if not row:
        return False
    return row[0].strip().lower() in ('name', 'id', 'program', 'applicant', 'name_ru', 'название', 'physics_or_ict', 'applicant_id')


def _row_program(row):
    name = str(row[0]).strip()
    try:
        budget_seats = int(row[1])
    except (ValueError, TypeError):
        budget_seats = 0
    return [name, budget_seats]


def _row_application(row):
    try:
        applicant_id = int(row[0])
        program_id = int(row[1])
        priority = int(row[3])
        consent = int(row[4])
    except (ValueError, TypeError):
        return None
    date = str(row[2]).strip()
    return [applicant_id, program_id, date, priority, consent]


def _row_applicant(row):
    try:
        return [int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])]
    except (ValueError, TypeError):
        return None


def _is_header_fio(row):
    if not row or len(row) < 2:
        return False
    return row[0].strip().lower() in ('фио', 'fio')


def import_applications_fio(db, file):
    with open(file, 'r', encoding='utf-8') as f:
        data = list(csv.reader(f))
    if not data or len(data) < 2:
        return
    skip = 1 if _is_header_fio(data[0]) else 0
    programs = db.get_program()
    def program_id_by_name(name):
        for r in programs:
            if r[1] == name.strip():
                return r[0]
        db.add_programs([[name.strip(), 0]])
        programs.clear()
        programs.extend(db.get_program())
        return programs[-1][0]
    for row in data[skip:]:
        if len(row) < 4:
            continue
        fio = str(row[0]).strip()
        try:
            score = int(row[1])
        except (ValueError, TypeError):
            continue
        date = str(row[2]).strip()
        op_name = str(row[3]).strip()
        pid = program_id_by_name(op_name)
        db.cur.execute(
            "INSERT INTO applicants (fio, physics_or_ict, russian, math, individual_achievements, total_score) VALUES (?, ?, ?, ?, ?, ?)",
            (fio, 0, 0, 0, 0, score)
        )
        aid = db.cur.lastrowid
        db.add_application([[aid, pid, date, 1, 1]])
        if db.autosave:
            db.con.commit()