import sqlite3
from .db_item import DBItem

ANALYSIS_MACHINE_CODE = 'ANALYSIS'


class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str):
        super().__init__('analyses', id, name)
        self.description = description

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ? WHERE fid = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_analyses(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT id, name, description FROM analyses')
    return {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description']
    ) for row in curs.fetchall()}


def insert_analysis(db_path: str, name: str, description: str) -> Analysis:

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description) VALUES (?, ?)', [name, description])
            id = curs.lastrowid
            result = Analysis(id, name, description)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result
