import json
import sqlite3
from enum import IntEnum

from qgis.core import QgsVectorLayer

from .db_item import DBItem


class Profile(DBItem):
    """ class to store long profile database item"""

    PROFILE_MACHINE_CODE = 'Profile'

    class ProfileTypes(IntEnum):

        GENERIC_PROFILE_TYPE = 1
        CENTERLINE_PROFILE_TYPE = 2
        THALWEG_PROFILE_TYPE = 3

    def __init__(self, id: int, name: str, profile_type_id: int, description: str, metadata: dict = None):
        super().__init__('profiles', id, name)
        self.profile_type_id = profile_type_id
        self.description = description
        self.metadata = metadata
        self.icon = 'line'
        self.fc_name = 'profile_centerlines' if profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE else 'profile_features'
        self.fc_id_column_name = 'profile_id'

    def feature_count(self, db_path: str) -> int:
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')
        return temp_layer.featureCount()


    def update(self, db_path: str, name: str, description: str, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE profiles SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex


def load_profiles(curs: sqlite3.Cursor) -> dict:  # profile_types: dict

    curs.execute("""SELECT * FROM profiles""")
    return {row['id']: Profile(
        row['id'],
        row['name'],
        row['profile_type_id'],  # profile_types[row['profile_type_id']],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}


def insert_profile(db_path: str, name: str, profile_type_id: int, description: str, metadata: str = None) -> Profile:

    profile = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO profiles (name, profile_type_id, description, metadata) VALUES (?, ?, ?,?)', [name, profile_type_id, description, metadata_str])
            id = curs.lastrowid
            profile = Profile(id, name, profile_type_id, description, metadata)
            conn.commit()

        except Exception as ex:
            profile = None
            conn.rollback()
            raise ex

    return profile
