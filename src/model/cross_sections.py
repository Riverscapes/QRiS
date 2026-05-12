import json
import sqlite3
from typing import Dict

from qgis.core import QgsDistanceArea, QgsProject, QgsUnitTypes

from .db_item_spatial import DBItemSpatial


class CrossSections(DBItemSpatial):
    """ class to store cross sections database item"""

    CROSS_SECTIONS_MACHINE_CODE = 'Cross Sections'

    def __init__(self, id: int, name: str, description: str, metadata: dict = None):
        super().__init__('cross_sections', id, name, 'cross_section_features', 'cross_section_id', 'LineString', metadata=metadata)
        self.description = description
        self.icon = 'line'

    def get_spatial_stats(self, db_path: str) -> dict:
        temp_layer = self.get_temp_layer(db_path)
        da = QgsDistanceArea()
        da.setSourceCrs(temp_layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())

        total_length = 0.0
        min_length = None
        max_length = None
        count = 0
        for feature in temp_layer.getFeatures():
            length = da.convertLengthMeasurement(da.measureLength(feature.geometry()), QgsUnitTypes.DistanceMeters)
            total_length += length
            min_length = length if min_length is None else min(min_length, length)
            max_length = length if max_length is None else max(max_length, length)
            count += 1

        return {
            'feature_count': count,
            'total_length': total_length,
            'average_length': total_length / count if count > 0 else 0.0,
            'min_length': min_length if min_length is not None else 0.0,
            'max_length': max_length if max_length is not None else 0.0,
        }


    def update(self, db_path: str, name: str, description: str, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE cross_sections SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id, ])
                conn.commit()

                self.name = name
                self.description = description
                self.set_metadata(metadata)

            except Exception as ex:
                conn.rollback()
                raise ex


def load_cross_sections(curs: sqlite3.Cursor) -> Dict[int, CrossSections]:

    curs.execute("""SELECT * FROM cross_sections""")
    return {row['id']: CrossSections(
        row['id'],
        row['name'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}


def insert_cross_sections(db_path: str, name: str, description: str, metadata: dict = None) -> CrossSections:

    cross_sections = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO cross_sections (name, description, metadata) VALUES (?, ?, ?)', [name, description, metadata_str])
            id = curs.lastrowid
            cross_sections = CrossSections(id, name, description, metadata)
            cross_sections.create_spatial_view(curs)
            conn.commit()
        except Exception as ex:
            conn.rollback()
            raise Exception(f"Error inserting cross sections {name}: {ex}") from ex

    return cross_sections
