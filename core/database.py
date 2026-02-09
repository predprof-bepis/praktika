import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from dbtools import DB


class DBManager:
    def __init__(self, fileName="../database.db"):
        self.fileName = fileName
        self.db = DB(self.fileName)

        self.places_count = {
            "pm": 40,
            "ivt": 50,
            "itss": 30,
            "ib": 20
        }

    def get_available_dates(self) -> list:
        res = self.db.run('''
            SELECT DISTINCT date FROM applications
        ''')
        return res


    def db_filter(self, programs: list, date="2026-08-04", onlyId=False) -> dict:
        res = dict()
        for program in programs:
            if not onlyId:
                res[program] = self.db.run('''
                        SELECT applicant_id, consent, priority, total_score FROM applications
                        LEFT JOIN applicants ON applications.applicant_id = applicants.id
                        WHERE date = ? AND
                        program_id = (
                            SELECT id FROM programs
                            WHERE name = ?
                        )
                    ''', date, program)
            else:
                res[program] = self.db.run('''
                    SELECT applicant_id FROM applications
                    WHERE date = ? AND program_id = (
                        SELECT id FROM programs 
                        WHERE name = ?                       
                    )
                ''', date, program)
            
        return res

    def get_applications_for_date(self, date):
        return self.db.run('''
            SELECT a.applicant_id, a.program_id, a.priority, a.consent, ap.total_score
            FROM applications a
            JOIN applicants ap ON a.applicant_id = ap.id
            WHERE a.date = ?
        ''', date)

    def _compute_global_enrollment(self, date):
        rows = self.get_applications_for_date(date)
        programs_rows = self.db.run('SELECT id, name, budget_seats FROM programs')
        pid_to_name = {r[0]: r[1] for r in programs_rows}
        budget = {r[0]: r[2] for r in programs_rows}
        places_left = dict(budget)

        with_consent = [(aid, pid, prio, cons, score) for aid, pid, prio, cons, score in rows if cons]
        enrolled = {}
        by_program = {pid: [] for pid in budget}

        for priority in [1, 2, 3, 4]:
            cand = [(r[0], r[1], r[4]) for r in with_consent if r[2] == priority and r[0] not in enrolled]
            cand.sort(key=lambda x: (-x[2], x[0]))
            for aid, pid, score in cand:
                if pid not in places_left or places_left[pid] <= 0:
                    continue
                enrolled[aid] = pid
                by_program[pid].append({"applicant_id": aid, "total_score": score, "priority": priority})
                places_left[pid] -= 1

        pass_scores = {}
        for pid, name in pid_to_name.items():
            lst = by_program.get(pid, [])
            if len(lst) < self.places_count.get(name, 0):
                pass_scores[name] = None
            else:
                pass_scores[name] = min(r["total_score"] for r in lst) if lst else None
        return pass_scores, by_program

    def count_accepted(self, data):
        count = 0
        for i in data:
            if i[1] == 1:
                count += 1
        return count

    def count_pass_score(self, programs: list, date: str = None, data: dict = None):
        if date is None and data:
            return {p: "НЕДОБОР" for p in programs}
        use_date = date
        if use_date is None:
            dates = self.db.run("SELECT DISTINCT date FROM applications")
            use_date = dates[0][0] if dates else None
        if use_date is None:
            return {p: "НЕДОБОР" for p in programs}
        pass_scores, _ = self._compute_global_enrollment(use_date)
        return {
            p: (pass_scores.get(p) if pass_scores.get(p) is not None else "НЕДОБОР")
            for p in programs
        }

    def get_places(self, programs: list, data: dict):
        res = {}
        for program in data.keys():
            res[program] = len(data[program])

        return res