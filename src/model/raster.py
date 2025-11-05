import os
import json
import sqlite3
from enum import Enum
from typing import Dict

from qgis.core import QgsRasterLayer
from .db_item import DBItem


BASEMAP_MACHINE_CODE = 'BASEMAP'
PROTOCOL_BASEMAP_MACHINE_CODE = 'PROTOCOL_BASEMAP'
SURFACE_MACHINE_CODE = 'SURFACE'
CONTEXT_MACHINE_CODE = 'CONTEXT'
CONTEXT_PARENT_FOLDER = 'context'
SURFACES_PARENT_FOLDER = 'surfaces'

# RASTER_TYPE_BASEMAP = 2
# RASTER_TYPE_SURFACE = 3
# RASTER_TYPE_CONTEXT = 4

RASTER_SLIDER_MACHINE_CODE = 'RASTER_SLIDER'


class Raster(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, raster_type_id: int, description: str, is_context=False, metadata=None):
        super().__init__('rasters', id, name)
        self.path = relative_project_path
        self.raster_type_id = raster_type_id
        self.is_context = is_context
        self.description = description
        self.icon = 'raster'
        self.metadata: dict = metadata

        self.date = self.metadata.get('system', {}).get('date', None) if self.metadata else None

    def update(self, db_path: str, name: str, description: str = None, metadata=None, raster_type_id=None) -> None:

        # setup the output data. Do not change the raster object until the transaction is successful
        out_metadata = metadata if metadata is not None else self.metadata
        out_raster_type_id = raster_type_id if raster_type_id else self.raster_type_id
        metadata_str = json.dumps(out_metadata)
        out_description = description if len(description) > 0 else self.description

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE rasters SET name = ?, description = ?, metadata = ?, raster_type_id = ? WHERE id = ?', [
                    name, out_description, metadata_str, out_raster_type_id, self.id])
                conn.commit()

                # Now update the raster object
                self.name = name
                self.description = out_description
                self.metadata = out_metadata
                self.raster_type_id = out_raster_type_id
                self.date = self.metadata.get('system', {}).get('date', None) if self.metadata else None

            except Exception as ex:
                conn.rollback()
                raise ex

    def delete(self, db_path: str) -> None:

        absolute_path = os.path.join(os.path.dirname(db_path), self.path)

        if os.path.isfile(absolute_path):
            raster = QgsRasterLayer(absolute_path)
            raster.dataProvider().remove()

        super().delete(db_path)


def load_rasters(curs: sqlite3.Cursor) -> Dict[int, Raster]:

    curs.execute('SELECT * FROM rasters')
    return {row['id']: Raster(
        row['id'],
        row['name'],
        row['path'],
        row['raster_type_id'],
        row['description'],
        bool(row['is_context']),
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


def insert_raster(db_path: str, name: str, path: str, raster_type_id: int, description: str, is_context: bool, metadata: dict = None) -> Raster:

    metadata_str = json.dumps(metadata) if metadata else None

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO rasters (name, path, raster_type_id, description, is_context, metadata) VALUES (?, ?, ?, ?, ?, ?)', [name, path, raster_type_id, description, int(is_context), metadata_str])
            id = curs.lastrowid
            result = Raster(id, name, path, raster_type_id, description, is_context=is_context, metadata=metadata)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result


def get_raster_symbology(db_path: str, raster_type_id: int) -> dict:

    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute('SELECT symbology FROM lkp_raster_types WHERE id = ?', [raster_type_id, ])
        result = curs.fetchone()
        if result:
            return result[0]
        else:
            return None
