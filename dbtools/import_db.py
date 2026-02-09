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
    contest_list = 4

class Importer:
    def __init__(self, db, table, mode, merge=False):
        self.db = db
        self.table = table
        self.mode = mode
        self.merge = merge

    def import_db(self, file):
        if self.mode != Mode.csv:
            return
        with open(file, 'r', encoding='utf-8') as f:
            data = list(csv.reader(f))
        if not data:
            return
        if self.table == Table.programs:
            data = data[1:] if _is_header(data[0]) else data
            rows = _rows_programs(data)
            if not rows:
                return
            # если в CSV есть id, вставляем его явно
            if len(rows[0]) == 3:
                self.db.run_many(
                    "INSERT INTO programs (id, name, budget_seats) VALUES (?, ?, ?)",
                    *rows
                )
            else:
                self.db.add_programs(rows)
        elif self.table == Table.applications:
            data = data[1:] if _is_header(data[0]) else data
            rows = _rows_application(data, self.db)
            if not rows:
                return
            # простой импорт таблицы applications, с учётом id при наличии
            if len(rows[0]) == 6:
                self.db.run_many(
                    "INSERT INTO applications (id, applicant_id, program_id, date, priority, consent) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    *rows
                )
            else:
                self.db.run_many(
                    "INSERT INTO applications (applicant_id, program_id, date, priority, consent) "
                    "VALUES (?, ?, ?, ?, ?)",
                    *rows
                )
        elif self.table == Table.applicants:
            data = data[1:] if _is_header(data[0]) else data
            rows = _rows_applicant(data)
            if not rows:
                return
            # applicants: либо без id, либо с id в первой колонке
            if len(rows[0]) == 6:
                self.db.run_many(
                    "INSERT INTO applicants (id, physics_or_ict, russian, math, individual_achievements, total_score) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    *rows
                )
            else:
                self.db.add_applicant(rows)
        elif self.table == Table.contest_list:
            data = data[1:] if _is_header(data[0]) else data
            _import_contest_list(self.db, data)


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
        # формат: name, budget_seats
        if len(i) == 2:
            name, seats = i[0], i[1]
            if not seats.isdecimal():
                continue
            final.append([name, int(seats)])
        # формат: id, name, budget_seats
        elif len(i) >= 3:
            pid, name, seats = i[0], i[1], i[2]
            if not pid.isdecimal() or not seats.isdecimal():
                continue
            final.append([int(pid), name, int(seats)])
    return final

def _rows_application(rows, db):
    final = []
    for i in rows:
        if len(i) not in (5, 6):
            continue

        # 5 колонок: applicant_id, program_id, date, priority, consent
        if len(i) == 5:
            aid, prog, date_str, prio, cons = i
            if not aid.isdecimal() or not prio.isdecimal() or not cons.isdecimal():
                continue
            try:
                date_val = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue
            if prog.isdecimal():
                program_id = int(prog)
            else:
                program_id = db.run("SELECT id FROM programs WHERE name = ?", prog)[0][0]
            final.append([int(aid), program_id, date_val, int(prio), int(cons)])
        # 6 колонок: id, applicant_id, program_id, date, priority, consent
        else:
            rid, aid, prog, date_str, prio, cons = i[0], i[1], i[2], i[3], i[4], i[5]
            if not rid.isdecimal() or not aid.isdecimal() or not prio.isdecimal() or not cons.isdecimal():
                continue
            try:
                date_val = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue
<<<<<<< Updated upstream

            final.append([
                          int(i[0]),
                          int(i[1]),
                          int(i[2]) if i[2].isdec                          datetime.strptime(i[2], "%Y-%m-%d"),
                          int(i[3]),imal() else db.run("SELECT id FROM programs WHERE name = ?", i[2])[0][0],
                          datetime.strptime(i[3], "%Y-%m-%d"),
                          int(i[4]),
                          int(i[5])
                          ])
=======
            if prog.isdecimal():
                program_id = int(prog)
            else:
                program_id = db.run("SELECT id FROM programs WHERE name = ?", prog)[0][0]
            final.append([int(rid), int(aid), program_id, date_val, int(prio), int(cons)])
>>>>>>> Stashed changes
    return final


def _rows_applicant(rows):
    final = []
    for row in rows:
<<<<<<< Updated upstream
        if len(row) != 5:
            try:
                return [int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])]
=======
        # 5 колонок: physics_or_ict, russian, math, individual_achievements, total_score
        if len(row) == 5:
            try:
                final.append([
                    int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])
                ])
>>>>>>> Stashed changes
            except (ValueError, TypeError):
                continue
        # 4 колонки: без total_score — считаем сами
        elif len(row) == 4:
            try:
<<<<<<< Updated upstream
                return [int(row[0]), int(row[1]), int(row[2]), int(row[3]), sum([int(row[0]), int(row[1]), int(row[2]), int(row[3])])]
=======
                p, r, m, ia = int(row[0]), int(row[1]), int(row[2]), int(row[3])
                total = p + r + m + ia
                final.append([p, r, m, ia, total])
            except (ValueError, TypeError):
                continue
        # 6 колонок: id, physics_or_ict, russian, math, individual_achievements, total_score
        elif len(row) >= 6:
            try:
                aid = int(row[0])
                p = int(row[1])
                r = int(row[2])
                m = int(row[3])
                ia = int(row[4])
                total = int(row[5])
                final.append([aid, p, r, m, ia, total])
>>>>>>> Stashed changes
            except (ValueError, TypeError):
                continue
    return final


def _import_contest_list(db, rows):
    """
    Импорт CSV в формате contest_list (как мы его экспортируем):
    applicant_id, program, date, priority, consent,
    total_score, physics_or_ict, russian, math, individual_achievements

    На основе него заполняем applicants + applications.
    """
    applications = []
    for r in rows:
        if len(r) < 10:
            continue
        aid, program, date_str, prio, cons, total, phys, rus, math, ia = r[:10]
        if not aid.isdecimal() or not prio.isdecimal() or not cons.isdecimal():
            continue
        try:
            date_val = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue

        # программа по имени (или id)
        if program.isdecimal():
            pid = int(program)
            prog_row = db.run("SELECT id FROM programs WHERE id = ?", pid)
            if not prog_row:
                # если такой программы нет — создаём с нулевыми местами
                db.run("INSERT INTO programs (id, name, budget_seats) VALUES (?, ?, ?)", pid, f"prog_{pid}", 0)
        else:
            prog_row = db.run("SELECT id FROM programs WHERE name = ?", program)
            if prog_row:
                pid = prog_row[0][0]
            else:
                db.run("INSERT INTO programs (name, budget_seats) VALUES (?, ?)", program, 0)
                pid = db.run("SELECT id FROM programs WHERE name = ?", program)[0][0]

        # абитуриент по id: либо обновляем, либо создаём
        if all(x.isdecimal() for x in (total, phys, rus, math, ia)):
            total_i = int(total)
            phys_i = int(phys)
            rus_i = int(rus)
            math_i = int(math)
            ia_i = int(ia)
        else:
            continue

        exists = db.run("SELECT 1 FROM applicants WHERE id = ?", int(aid))
        if exists:
            db.run(
                "UPDATE applicants SET physics_or_ict = ?, russian = ?, math = ?, "
                "individual_achievements = ?, total_score = ? WHERE id = ?",
                phys_i, rus_i, math_i, ia_i, total_i, int(aid)
            )
        else:
            db.run(
                "INSERT INTO applicants (id, physics_or_ict, russian, math, individual_achievements, total_score) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                int(aid), phys_i, rus_i, math_i, ia_i, total_i
            )

        applications.append(
            (int(aid), pid, date_val, int(prio), int(cons))
        )

    if applications:
        db.run_many(
            "INSERT INTO applications (applicant_id, program_id, date, priority, consent) "
            "VALUES (?, ?, ?, ?, ?)",
            *applications
        )


def _merge_applications(db, rows):
    if not rows:
        return
    dates = list({r[2] for r in rows})
    date_strs = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in dates]

    existing = db.run(
        "SELECT applicant_id, program_id, date FROM applications WHERE date IN (" + ",".join("?" * len(date_strs)) + ")",
        *date_strs
    )
    existing_set = set()
    for r in existing:
        dt = r[2]
        if hasattr(dt, "strftime"):
            dt = dt.strftime("%Y-%m-%d")
        existing_set.add((r[0], r[1], str(dt)))

    in_file = set()
    row_by_key = {}
    for r in rows:
        applicant_id, program_id, date_val, priority, consent = r[0], r[1], r[2], r[3], r[4]
        dt_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)
        key = (applicant_id, program_id, dt_str)
        in_file.add(key)
        row_by_key[key] = r

    to_delete = existing_set - in_file
    to_add = in_file - existing_set
    to_update = existing_set & in_file

    if to_delete:
        for aid, pid, dt in to_delete:
            db.run(
                "DELETE FROM applications WHERE applicant_id = ? AND program_id = ? AND date = ?",
                aid, pid, dt
            )
    if to_add:
        db.add_application([row_by_key[k] for k in to_add])
    if to_update:
        app_ids = db.run(
            "SELECT id, applicant_id, program_id, date FROM applications WHERE date IN (" + ",".join("?" * len(date_strs)) + ")",
            *date_strs
        )
        key_to_id = {}
        for row in app_ids:
            dt = row[3]
            if hasattr(dt, "strftime"):
                dt = dt.strftime("%Y-%m-%d")
            key_to_id[(row[1], row[2], str(dt))] = row[0]
        for key in to_update:
            r = row_by_key[key]
            app_id = key_to_id.get(key)
            if app_id is not None:
                db.run(
                    "UPDATE applications SET applicant_id = ?, program_id = ?, date = ?, priority = ?, consent = ? WHERE id = ?",
                    r[0], r[1], r[2], r[3], r[4], app_id
                )


def _merge_applicants(db, rows):
    if not rows:
        return
    existing = db.run("SELECT 1 FROM applicants LIMIT 1")
    if not existing:
        db.add_applicant(rows)
