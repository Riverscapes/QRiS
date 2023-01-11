import os
import sqlite3
from qgis.core import QgsRasterLayer
from .db_item import DBItem


BASEMAP_MACHINE_CODE = 'BASEMAP'
PROTOCOL_BASEMAP_MACHINE_CODE = 'PROTOCOL_BASEMAP'
SURFACE_MACHINE_CODE = 'SURFACE'
CONTEXT_MACHNINE_CODE = 'CONTEXT'
BASEMAP_PARENT_FOLDER = 'basemaps'
SCRATCH_PARENT_FOLDER = 'scratch'

RASTER_TYPE_BASEMAP = 2
RASTER_TYPE_SURFACE = 3

RASTER_SLIDER_MACHINE_CODE = 'RASTER_SLIDER'


class Raster(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, raster_type_id: int, description: str):
        super().__init__('rasters', id, name)
        self.path = relative_project_path
        self.raster_type_id = raster_type_id
        self.description = description
        self.icon = 'basemap'

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE rasters SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
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


def load_rasters(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM rasters')
    return {row['id']: Raster(
        row['id'],
        row['name'],
        row['path'],
        row['raster_type_id'],
        row['description']
    ) for row in curs.fetchall()}


def insert_raster(db_path: str, name: str, path: str, raster_type_id: int, description: str) -> Raster:

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO rasters (name, path, raster_type_id, description) VALUES (?, ?, ?, ?)', [name, path, raster_type_id, description])
            id = curs.lastrowid
            result = Raster(id, name, path, raster_type_id, description)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result
