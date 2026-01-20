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
