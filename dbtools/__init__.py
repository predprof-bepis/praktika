# run_many быстрее, но он работает только с
# INSERT
# UPDATE
# DELETE
# REPLACE
# Для всех остальных нужно использовать run
import sqlite3


class DB:
    def __init__(self, filename="database.db", autosave=True):
        # Локальные переменные
        self.con = sqlite3.connect(filename)
        self.cur = self.con.cursor()
        self.autosave = autosave

        # Set up
        self.create_tables()

    def create_tables(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            physics_or_ict INTEGER NOT NULL,
            russian INTEGER NOT NULL,
            math INTEGER NOT NULL,
            individual_achievements INTEGER NOT NULL,
            total_score INTEGER NOT NULL
        );""")
        try:
            self.cur.execute("ALTER TABLE applicants ADD COLUMN fio TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        self.cur.execute("""CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            budget_seats INTEGER NOT NULL
        );""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER NOT NULL,
            program_id INTEGER NOT NULL,
            date DATE NOT NULL,
            priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 4),
            consent INTEGER NOT NULL,
        
            UNIQUE (applicant_id, program_id, date),
        
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (program_id) REFERENCES programs(id)
        );""")

        if self.autosave:
            self.con.commit()

    # Работа с программами
    def get_program(self, idx=None):
        '''без аргумента - все заявления,
           с аргументом числом - найти запись с id как аргумент'''
        if idx is None:
            return self.run("SELECT * FROM programs;")
        else:
            return self.run("SELECT * FROM programs WHERE id = ?;", idx)

    def add_programs(self, data):
        '''в data указывать в списке записи
           [<name>, <budget_seats>] - пример запись'''
        if not data:
            return
        self.run_many("INSERT INTO programs (name, budget_seats) VALUES (?, ?)", *data)
        self.remove_duplicate_programs()

    def remove_duplicate_programs(self):
        self.cur.execute("""DELETE FROM programs WHERE id IN (
            SELECT p1.id FROM programs p1
            INNER JOIN programs p2 ON p1.name = p2.name AND p1.id > p2.id
        )""")
        if self.autosave:
            self.con.commit()

    def update_program_by_id(self, data):
        '''в дата указывать\n
           [<name (можно менять)>, <budget seats (можно менять)>, id записи] - пример одной записи\n
           подавать в списке\n'''
        self.run_many("UPDATE programs SET name = ?, budget_seats = ? WHERE id = ?", *data)

    # Работа с заявлениями
    def get_application(self, idx=None):
        '''без аргумента - все заявления,
           с аргументом числом - найти запись с id как аргумент'''
        if idx is None:
            return self.run("SELECT * FROM applications;")
        else:
            return self.run("SELECT * FROM applications WHERE id = ?;", idx)

    def add_application(self, data):
        '''в дата указывать\n
           [<applicant_id>, <program_id>, <date>, <priority>, <consent>] - пример одной записи\n
           подавать в списке\n
        '''
        self.run_many("INSERT INTO applications (applicant_id, program_id, date, priority, consent) VALUES (?, ?, ?, ?, ?)", *data)

    def update_application_by_id(self, data):
        '''в дата указывать\n
           [<applicant_id>, <program_id>, <date>, <priority>, <consent>, id записи] - пример одной записи\n
           подавать в списке\n'''
        self.run_many("UPDATE applications SET applicant_id = ?, program_id = ?, date = ?, priority = ?, consent = ? WHERE id = ?", *data)

    # Работа с заявителями
    def get_applicant(self, idx=None):
        '''без аргумента - все заявления,
           с аргументом числом - найти запись с id как аргумент'''
        if idx is None:
            return self.run("SELECT * FROM applicants;")
        else:
            return self.run("SELECT * FROM applicants WHERE id = ?;", idx)

    def add_applicant(self, data):
        '''в data указывать [<fio>, <physics_or_ict>, <russian>, <math>, <individual_achievements>, <total_score>]'''
        self.run_many("INSERT INTO applicants (fio, physics_or_ict, russian, math, individual_achievements, total_score) VALUES (?, ?, ?, ?, ?, ?)", *data)

    def update_aplicant_by_id(self, data):
        '''в дата указывать\n
           [<physics_or_ict>, <russian>, <math>, <individual_achievements>, <total_score>, id записи] - пример одной записи\n
           подавать в списке\n'''
        self.run_many("UPDATE applicants SET physics_or_ict = ?, russian = ?, math = ?, individual_achievements = ?, total_score = ? WHERE id = ?", *data)


    def run(self, query, *args):
        self.cur.execute(query, tuple(args))
        if self.autosave:
            self.con.commit()
        return self.cur.fetchall()

    def run_many(self, query, *args):
        self.cur.executemany(query, tuple(args))
        if self.autosave:
            self.con.commit()
        return self.cur.fetchall()