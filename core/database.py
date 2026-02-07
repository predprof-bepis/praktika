import sys
import os


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


from dbtools import DB


class DBManager:
    def __init__(self, fileName="database.db"):
        self.fileName = fileName
        self.db = DB(self.fileName)
