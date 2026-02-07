import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from dbtools import DB


class DBManager:
    def __init__(self, fileName="database.db"):
        self.fileName = fileName
        self.db = DB(self.fileName)

        self.places_count = {
            "pm": 40,
            "ivt": 50,
            "itss": 30,
            "ib": 20
        }

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
    
    def _compare_applicants(self, applicant1: tuple, applicant2: tuple):
            if applicant1[1] > applicant2[1]:
                return 1
            elif applicant1[1] < applicant2[1]:
                return -1
            else:
                if applicant1[2] < applicant2[2]:
                    return -1
                elif applicant1[2] > applicant2[2]:
                    return 1
                else:
                    return 0
                
    def count_accepted(self, data: list[tuple[int, int, int]]):
        count = 0
        for i in data:
            if i[1] == 1:
                count += 1

        return count

    def count_pass_score(self, programs: list, data: dict):
        '''Подсчет проходного балла для каждой программы. data ужен обязательно с данными
        из столбцов consent и total_score'''
        from functools import cmp_to_key


        res = dict()
        for program in programs:
            if program not in data.keys():
                continue

            program_data = data[program]
            program_data = sorted(program_data, key=cmp_to_key(self._compare_applicants), reverse=True)

            accepted = self.count_accepted(program_data)
            if accepted >= self.places_count[program]:
                res[program] = 0 # все места уже заняты
                continue
            else:
                try: # подают больше заявок, чем мест
                    score = program_data[self.places_count[program] - 1][2]
                except IndexError:
                    score = program_data[-1][2]

            res[program] = score

        return res