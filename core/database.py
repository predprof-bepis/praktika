import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from dbtools import DB


class DBManager:
    def __init__(self, fileName="database.db"):
        self.fileName = fileName
        self.db = DB(self.fileName)

    def db_filter(self, programs: list, date="2026-08-04") -> dict:
        res = dict()
        for program in programs:
            res[program] = self.db.run('''
                    SELECT applicant_id, consent, total_score FROM applications
                    LEFT JOIN applicants ON applications.applicant_id = applicants.id
                    WHERE date = ? AND
                    program_id = (
                        SELECT id FROM programs
                        WHERE name = ?
                    )
                ''', date, program)
            
        return res
