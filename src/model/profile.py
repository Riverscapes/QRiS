import sqlite3
from enum import IntEnum

from .db_item import DBItem


class Profile(DBItem):
    """ class to store long profile database item"""

    PROFILE_MACHINE_CODE = 'Profile'

    class ProfileTypes(IntEnum):

        GENERIC_PROFILE_TYPE = 1
        CENTERLINE_PROFILE_TYPE = 2
        THALWEG_PROFILE_TYPE = 3

    def __init__(self, id: int, name: str, profile_type_id: int, description: str):
        super().__init__('profiles', id, name)
        self.profile_type_id = profile_type_id
        self.description = description
        self.icon = 'gis'

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE profiles SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_profiles(curs: sqlite3.Cursor) -> dict:  # profile_types: dict

    curs.execute("""SELECT * FROM profiles""")
    return {row['id']: Profile(
        row['id'],
        row['name'],
        row['profile_type_id'],  # profile_types[row['profile_type_id']],
        row['description']
    ) for row in curs.fetchall()}


def insert_profile(db_path: str, name: str, profile_type_id: int, description: str, metadata: str = None) -> Profile:

    profile = None
    description = description if len(description) > 0 else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO profiles (name, profile_type_id, description, metadata) VALUES (?, ?, ?,?)', [name, profile_type_id, description, metadata])
            id = curs.lastrowid
            profile = Profile(id, name, profile_type_id, description)
            conn.commit()

        except Exception as ex:
            mask = None
            conn.rollback()
            raise ex

    return profile
