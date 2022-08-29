import sqlite3
from .db_item import DBItem


class Metric(DBItem):

    def __init__(self, id: int, name: str, description: str, default_level_id: int):
        super().__init__('metrics', id, name)
        self.description = description
        self.default_level_id = default_level_id
        self.icon = 'metric'


def load_metrics(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM metrics')
    return {row['id']: Metric(
        row['id'],
        row['name'],
        row['description'],
        row['default_level_id']
    ) for row in curs.fetchall()}
