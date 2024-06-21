import json
import sqlite3

from qgis.core import QgsVectorLayer

from .db_item import DBItem


class ValleyBottom(DBItem):
    """ class to store valley bottom database item"""

    VALLEY_BOTTOM_MACHINE_CODE = 'Valley Bottom'

    def __init__(self, id: int, name: str, description: str, metadata: dict = None):
        super().__init__('valley_bottoms', id, name)
        self.description = description
        self.metadata = metadata
        self.icon = 'polygon'
        self.fc_name = 'valley_bottom_features'
        self.fc_id_column_name = 'valley_bottom_id'

    def feature_count(self, db_path: str) -> int:
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')
        return temp_layer.featureCount()


    def update(self, db_path: str, name: str, description: str, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE valley_bottoms SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id, ])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex


def load_valley_bottoms(curs: sqlite3.Cursor) -> dict:

    curs.execute("""SELECT * FROM valley_bottoms""")
    return {row['id']: ValleyBottom(
        row['id'],
        row['name'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}


def insert_valley_bottom(db_path: str, name: str, description: str, metadata: dict = None) -> ValleyBottom:

    valley_bottom = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO valley_bottoms (name, description, metadata) VALUES (?, ?, ?)', [name, description, metadata_str])
            id = curs.lastrowid
            valley_bottom = ValleyBottom(id, name, description, metadata)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return valley_bottom
