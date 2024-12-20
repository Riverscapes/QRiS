import json
import sqlite3
from typing import Dict

from qgis.core import QgsVectorLayer

from .db_item import DBItem

SAMPLE_FRAME_MACHINE_CODE = 'Sample Frame'
AOI_MACHINE_CODE = 'AOI'
VALLEY_BOTTOM_MACHINE_CODE = 'Valley Bottom'

class SampleFrame(DBItem):

    SAMPLE_FRAME_TYPE = 1
    AOI_SAMPLE_FRAME_TYPE = 2
    VALLEY_BOTTOM_SAMPLE_FRAME_TYPE = 3

    def __init__(self, id: int, name: str, description: str, metadata: dict = None, sample_frame_type=SAMPLE_FRAME_TYPE):
        super().__init__('sample_frames', id, name)
        self.description = description
        self.metadata = metadata
        self.user_metadata = None
        self.fields = None
        self.default_flow_path_name = None
        self.sample_frame_type = sample_frame_type
        if metadata is not None:
            self.fields = metadata.get('fields', None)
            self.default_flow_path_name = metadata.get('default_flow_path_name', None)
            self.user_metadata = metadata.get('metadata', None)

        if self.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
            self.icon = 'mask'
        elif self.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
            self.icon = 'valley_bottom'
        else:
            self.icon = 'mask_regular'

        self.fc_name = 'sample_frame_features'
        self.fc_id_column_name = 'sample_frame_id'
    
    def feature_count(self, db_path: str) -> int:
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')
        return temp_layer.featureCount()


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


def load_sample_frames(curs: sqlite3.Cursor, sample_frame_type=SampleFrame.SAMPLE_FRAME_TYPE) -> dict:

    curs.execute("""SELECT * FROM sample_frames WHERE sample_frame_type_id = ?""", [sample_frame_type])
    return {row['id']: SampleFrame(
        row['id'],
        row['name'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None,
        row['sample_frame_type_id']
    ) for row in curs.fetchall()}


def insert_sample_frame(db_path: str, name: str, description: str, metadata: dict=None, sample_frame_type=SampleFrame.SAMPLE_FRAME_TYPE) -> SampleFrame:

    sample_frame = None
    sample_frame_type = sample_frame_type
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO sample_frames (name, description, metadata, sample_frame_type_id) VALUES (?, ?, ?, ?)', [name, description, metadata_str, sample_frame_type])
            id = curs.lastrowid
            sample_frame = SampleFrame(id, name, description, metadata, sample_frame_type)
            conn.commit()

        except Exception as ex:
            sample_frame = None
            conn.rollback()
            raise ex

    return sample_frame


def get_sample_frame_ids(db_path: str, sample_frame_id: int) -> Dict[int, DBItem]:

    labels = {}
    try:
        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            curs.execute('SELECT fid, display_label FROM sample_frame_features WHERE sample_frame_id = ?', [sample_frame_id])
            values = curs.fetchall()
            for value in values:
                label = value[1] if value[1] is not None and value[1] != '' else f'Feature {value[0]}'
                labels[label] =  DBItem('None', value[0], label)
    except Exception as ex:
        labels = {}
        raise ex

    return labels
