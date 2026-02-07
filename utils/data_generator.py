from dbtools import DB
import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


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


db = DB()
db.create_tables()

db.run('''
    DELETE FROM applicants
''')

applicants_data(db)
