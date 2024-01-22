import json
import sqlite3
from typing import Dict

from .db_item import DBItem

SAMPLE_FRAME_MACHINE_CODE = 'SampleFrame'

class SampleFrame(DBItem):

    def __init__(self, id: int, name: str, description: str, metadata: dict = None):
        super().__init__('sample_frames', id, name)
        self.description = description
        self.metadata = metadata
        self.user_metadata = None
        self.fields = None
        self.default_flow_path_name = None
        if metadata is not None:
            self.fields = metadata.get('fields', None)
            self.default_flow_path_name = metadata.get('default_flow_path_name', None)
            self.user_metadata = metadata.get('metadata', None)

        self.icon = 'mask_regular'
        self.fc_name = 'sample_frame_features'
        self.fc_id_column_name = 'sample_frame_id'

    def update(self, db_path: str, name: str, description: str, metadata: dict=None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE sample_frames SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata
                if metadata is not None:
                    self.fields = metadata.get('fields', None)
                    self.default_flow_path_name = metadata.get('default_flow_path_name', None)
                    self.user_metadata = metadata.get('metadata', None)

            except Exception as ex:
                conn.rollback()
                raise ex


def load_sample_frames(curs: sqlite3.Cursor) -> dict:

    curs.execute("""SELECT * FROM sample_frames""")
    return {row['id']: SampleFrame(
        row['id'],
        row['name'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}


def insert_sample_frame(db_path: str, name: str, description: str, metadata: dict=None) -> SampleFrame:

    sample_frame = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO sample_frames (name, description, metadata) VALUES (?, ?, ?)', [name, description, metadata_str])
            id = curs.lastrowid
            sample_frame = SampleFrame(id, name, description, metadata)
            conn.commit()

        except Exception as ex:
            sample_frame = None
            conn.rollback()
            raise ex

    return sample_frame


def get_sample_frame_ids(db_path: str, sample_frame_id: int) -> Dict[int, DBItem]:

    labels = None
    try:
        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            curs.execute('SELECT DISTINCT fid, display_label FROM sample_frame_features WHERE sample_frame_id = ?', [sample_frame_id])
            labels = {row[1]: DBItem('None', row[0], row[1]) for row in curs.fetchall()}
    except Exception as ex:
        labels = []
        raise ex

    return labels
