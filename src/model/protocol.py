import sqlite3
from .db_item import DBItem, dict_factory


class Protocol(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, description: str):
        super().__init__('protocols', id, name)
        self.description = description
        self.machine_code = machine_code


def load(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM protocols')
    return {row['id']: Protocol(
        row['id'],
        row['name'],
        row['machine_code'],
        row['description']
    ) for row in curs.fetchall()}
