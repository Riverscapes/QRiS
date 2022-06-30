import os
import sqlite3
from numpy import absolute
from osgeo import gdal
from qgis.core import QgsRasterLayer
from .db_item import DBItem, dict_factory


BASEMAP_MACHINE_CODE = 'BASEMAP'
PROTOCOL_BASEMAP_MACHINE_CODE = 'PROTOCOL_BASEMAP'
BASEMAP_PARENT_FOLDER = 'basemaps'


class Basemap(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, description: str):
        super().__init__('basemaps', id, name)
        self.path = relative_project_path
        self.description = description

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE basemaps SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex

    def delete(self, db_path: str) -> None:

        absolute_path = os.path.join(os.path.dirname(db_path), self.path)

        if os.path.isfile(absolute_path):
            raster = QgsRasterLayer(absolute_path)
            raster.dataProvider().remove()

        super().delete(db_path)


def load_basemaps(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT id, name, path, type, description FROM basemaps')
    return {row['id']: Basemap(
        row['id'],
        row['name'],
        row['path'],
        row['description']
    ) for row in curs.fetchall()}


def insert_basemap(db_path: str, name: str, path: str, description: str) -> Basemap:

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO basemaps (name, path, description) VALUES (?, ?, ?)', [name, path, description])
            id = curs.lastrowid
            result = Basemap(id, name, path, description)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result
