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
        self.cur.execute("""CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            budget_seats INTEGER NOT NULL
        );""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS applications (
            applicant_id INTEGER NOT NULL,
            program_id INTEGER NOT NULL,
            date DATE NOT NULL,
            priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 4),
            consent INTEGER NOT NULL,
        
            PRIMARY KEY (applicant_id, program_id, date),
        
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (program_id) REFERENCES programs(id)
        );""")

        if self.autosave:
            self.con.commit()

    # Работа с программами
    def get_program(self, idx=None):
        '''без аргумента - все записи,
           с аргументом - id записи программы'''
        if idx is None:
            return self.run("SELECT * FROM programs;")
        else:
            return self.run("SELECT * FROM programs WHERE id = ?;", idx)

    def add_programs(self, data):
        '''в data указывать в списке записи
           [<name>, <budget_seats>] - пример запись'''
        self.run_many("INSERT INTO programs (name, budget_seats) VALUES (?, ?)", *data)

    def update_program_by_id(self, data):
        '''в дата указывать
           [<name (можно менять)>, <budget seats (можно менять)>, id записи] - пример одной записи
           подавать в списке'''
        self.run_many("UPDATE programs SET name = ?, budget_seats = ? WHERE id = ?", *data)


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