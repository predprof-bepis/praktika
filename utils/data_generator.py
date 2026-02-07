import sys
import os
import random


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from dbtools import DB


def program_data(db):
    db.run('''
        INSERT INTO programs(name, budget_seats) 
        VALUES ("pm", 40)
    ''')
    db.run('''
        INSERT INTO programs(name, budget_seats) 
        VALUES ("ivt", 50)
    ''')
    db.run('''
        INSERT INTO programs(name, budget_seats) 
        VALUES ("itss", 30)
    ''')
    db.run('''
        INSERT INTO programs(name, budget_seats) 
        VALUES ("ib", 20)
    ''')


def applicants_data(db):
    for i in range(1, 101):
        helper = db.run('''
            INSERT INTO applicants (physics_or_ict, russian, math, individual_achievements, total_score) 
            VALUES(CAST(abs(random()) % 100 + 1 AS INTEGER), 
                CAST(abs(random()) % 100 + 1 AS INTEGER), 
                CAST(abs(random()) % 100 + 1 AS INTEGER), 
                CAST(abs(random()) % 100 + 1 AS INTEGER),
                    1)    
            ''')

    helper = db.run('''
        UPDATE applicants
        SET total_score = physics_or_ict + russian + math + individual_achievements
    ''')


def applications_data(db):
    for i in range(1, 101):
        program_id = random.randint(1, 4)
        many_programs = random.randint(0, 1)
        consent = random.randint(0, 1)
        helper = db.run('''
            INSERT INTO applications (applicant_id, program_id, date, priority, consent) 
            VALUES (?, ?, "2026-08-04", ?, ?)
        ''', i, program_id, program_id, consent) # пока что дата только 04.08

        if many_programs == 1:
            program_count = random.randint(1, 3) # на сколько программ подаемся

            already_applied = [program_id,]
            priority = program_id
            
            for i in range(program_count):
                program_id = 1
                while program_id in already_applied:
                    program_id += 1

                helper = db.run('''
                    INSERT INTO applications (applicant_id, program_id, date, priority, consent)
                    VALUES (?, ?, "2026-08-04", ?, ?)
                ''', i, program_id, priority, consent)

                already_applied.append(program_id)


db = DB()
db.create_tables()

# чистка
db.run('''DELETE FROM applicants''')
db.run('DELETE FROM sqlite_sequence WHERE name = "applicants"')

applicants_data(db)
program_data(db)
applications_data(db)