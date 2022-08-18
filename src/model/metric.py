import sqlite3
from .db_item import DBItem


class Metric(DBItem):

    def __init__(self, id: int, name: str, description: str):
        super().__init__('metrics', id, name)
        self.description = description
        self.icon = 'metric'


def load_metrics(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM metrics')
    return {row['id']: Metric(
        row['id'],
        row['name'],
        row['description']
    ) for row in curs.fetchall()}
