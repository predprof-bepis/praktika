import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from core.database import DBManager


db_manager = DBManager()


def get_scores(date):
    programs = ["pm", "ivt", "itss", "ib"]
    scores = db_manager.count_pass_score(programs, date=date)
    return scores


def get_dates():
    return db_manager.get_available_dates() 


def get_places_counts(date):
    programs = ["pm", "ivt", "itss", "ib"]
    data = db_manager.db_filter(programs, date)
    return db_manager.get_places(programs, data)


def get_data(date, program):
    return db_manager.db_filter(program, date)