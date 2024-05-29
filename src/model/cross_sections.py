import json
import sqlite3

from qgis.core import QgsVectorLayer

from .db_item import DBItem


class CrossSections(DBItem):
    """ class to store cross sections database item"""

    CROSS_SECTIONS_MACHINE_CODE = 'Cross Sections'

    def __init__(self, id: int, name: str, description: str, metadata: dict = None):
        super().__init__('cross_sections', id, name)
        self.description = description
        self.metadata = metadata
        self.icon = 'line'
        self.fc_name = 'cross_section_features'
        self.fc_id_column_name = 'cross_section_id'

    def feature_count(self, db_path: str) -> int:
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')
        return temp_layer.featureCount()


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
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex


def load_cross_sections(curs: sqlite3.Cursor) -> dict:

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
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return cross_sections
