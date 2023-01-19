import sqlite3

from .db_item import DBItem


class CrossSections(DBItem):
    """ class to store cross sections database item"""

    CROSS_SECTIONS_MACHINE_CODE = 'Cross Sections'

    def __init__(self, id: int, name: str, description: str):
        super().__init__('cross_sections', id, name)
        self.description = description
        self.icon = 'gis'

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE cross_sections SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_cross_sections(curs: sqlite3.Cursor) -> dict:

    curs.execute("""SELECT * FROM cross_sections""")
    return {row['id']: CrossSections(
        row['id'],
        row['name'],
        row['description']
    ) for row in curs.fetchall()}


def insert_cross_sections(db_path: str, name: str, description: str, metadata: str = None) -> CrossSections:

    cross_sections = None
    description = description if len(description) > 0 else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO cross_sections (name, description, metadata) VALUES (?, ?, ?)', [name, description, metadata])
            id = curs.lastrowid
            cross_sections = CrossSections(id, name, description)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return cross_sections
