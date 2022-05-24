import sqlite3
from .db_item import DBItem, dict_factory


BASEMAP_MACHINE_CODE = 'BASEMAP'
BASEMAP_PARENT_FOLDER = 'basemaps'


class Basemap(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, description: str):
        super().__init__(id, name)
        self.path = relative_project_path
        self.description = description

    def update(self, curs: sqlite3.Cursor, name: str, description: str) -> None:

        curs.execute('UPDATE bases SET name = ?, description = ?', [name, description])
        self.name = name
        self.description = description

    def delete(self, conn: sqlite3.Connection) -> None:
        curs = conn.cursor()
        curs.execute('DELETE FROM bases WHERE fid = ?', [self.id])


def load_basemaps(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT fid, name, path, type, description FROM bases')
    return {row['fid']: Basemap(
        row['id'],
        row['name'],
        row['path'],
        row['description']
    ) for row in curs.fetchall()}
