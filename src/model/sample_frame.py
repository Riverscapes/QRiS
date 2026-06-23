import json
import sqlite3
from typing import Dict, List

from .db_item import DBItem
from .db_item_spatial import DBItemSpatial 

SAMPLE_FRAME_MACHINE_CODE = 'Sample Frame'
AOI_MACHINE_CODE = 'AOI'
VALLEY_BOTTOM_MACHINE_CODE = 'Valley Bottom'

class SampleFrame(DBItemSpatial):

    SAMPLE_FRAME_TYPE = 1
    AOI_SAMPLE_FRAME_TYPE = 2
    VALLEY_BOTTOM_SAMPLE_FRAME_TYPE = 3

    FEATURE_FIELD_CONFIG = {
        'fields': [
            {'id': 'objective', 'type': 'long_text', 'label': 'Objective'},
            {'id': 'condition', 'type': 'long_text', 'label': 'Condition'},
        ]
    }

    def __init__(self, id: int, name: str, description: str, metadata: dict = None, sample_frame_type=SAMPLE_FRAME_TYPE):
        super().__init__('sample_frames', id, name, 'sample_frame_features', 'sample_frame_id', 'Polygon', metadata=metadata)
        
        self.description: str = description
        self.sample_frame_type = sample_frame_type

        if self.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
            self.icon = 'mask'
        elif self.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
            self.icon = 'valley_bottom'
        else:
            self.icon = 'mask_regular'

    def update(self, db_path: str, name: str, description: str, metadata: dict=None) -> None:

        description = description if description is not None and len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE sample_frames SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.set_metadata(metadata)

            except Exception as ex:
                conn.rollback()
                raise ex

    def set_metadata(self, metadata: dict) -> None:
        super().set_metadata(metadata)
        # special handling for sample frame items
        self.project_bounds = self.system_metadata.get('project_bounds', False)
        self.default_flow_path_name = self.metadata.get('default_flow_path_name', None)

        # Normalize category fields to canonical schema: {id, label, type, values}
        raw_fields = self.metadata.get('fields', None)
        if raw_fields:
            normalized = []
            for f in raw_fields:
                if isinstance(f, str):
                    # very old plain-string format
                    normalized.append({'id': f.lower().replace(' ', '_'), 'label': f, 'type': 'list', 'values': []})
                else:
                    n = dict(f)
                    # machine_code → id
                    if 'id' not in n and 'machine_code' in n:
                        n['id'] = n.pop('machine_code')
                    elif 'machine_code' in n:
                        del n['machine_code']
                    if 'type' not in n:
                        n['type'] = 'list'
                    if 'values' not in n:
                        n['values'] = []
                    normalized.append(n)
            self.fields = normalized
        else:
            self.fields = None


def load_sample_frames(curs: sqlite3.Cursor, sample_frame_type=SampleFrame.SAMPLE_FRAME_TYPE) -> Dict[int, SampleFrame]:

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
            sample_frame.create_spatial_view(curs)
            conn.commit()
        except Exception as ex:
            sample_frame = None
            conn.rollback()
            raise Exception(f"Error inserting sample frame {name}: {ex}") from ex
    return sample_frame


def get_sample_frame_ids(db_path: str, sample_frame_id: int) -> Dict[int, DBItem]:

    labels = {}
    try:
        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            curs.execute('SELECT fid, display_label FROM sample_frame_features WHERE sample_frame_id = ?', [sample_frame_id])
            values = curs.fetchall()
            used_names = set()
            for value in values:
                fid = value[0]
                label = value[1] if value[1] is not None and value[1] != '' else f'Feature {fid}'

                # Safeguard against duplicate display labels by disambiguating
                # only the duplicates while preserving all feature IDs.
                name = label
                if name in used_names:
                    name = f'{label} (Feature {fid})'
                used_names.add(name)

                labels[fid] = DBItem('None', fid, name)
    except Exception as ex:
        labels = {}
        raise ex

    return labels

def get_sample_frame_sequence(db_path: str, sample_frame_id: int) -> List[DBItem]:
    """
    Returns an ordered list of DBItems for the sample frame features.
    Tries flows_into, then display_label (if all are unique integers), then fid order.
    """
    sequence = []
    try:
        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            curs.execute('SELECT fid, display_label, flows_into FROM sample_frame_features WHERE sample_frame_id = ?', [sample_frame_id])
            values = curs.fetchall()
            fids = [v[0] for v in values]
            flows_into = [v[2] for v in values]
            display_labels = [v[1] for v in values]

            # 1. Try flows_into: build a chain if all flows_into are valid or null (last)
            flows_into_valid = (
                all((fi is None or fi in fids) for fi in flows_into) and
                len(values) == len(set(fids))
            )
            if flows_into_valid and any(fi is not None for fi in flows_into):
                referenced = set(fi for fi in flows_into if fi is not None)
                start_candidates = [fid for fid in fids if fid not in referenced]
                if len(start_candidates) == 1:
                    fid_to_next = {v[0]: v[2] for v in values}
                    fid_to_row = {v[0]: v for v in values}
                    fid = start_candidates[0]
                    visited = set()
                    while fid is not None:
                        if fid in visited:
                            # Cycle detected; method 1 is invalid and we should fallback.
                            sequence = []
                            break
                        visited.add(fid)
                        row = fid_to_row[fid]
                        sequence.append(DBItem('sample_frame_features', row[0], row[1]))
                        fid = fid_to_next.get(fid)
                    if len(sequence) == len(values):
                        return sequence
                    sequence = []

            # 2. Try display_label: all must be non-null, integer, and unique
            if (
                all(lbl is not None and str(lbl).isdigit() for lbl in display_labels) and
                len(set(int(lbl) for lbl in display_labels)) == len(display_labels)
            ):
                label_to_row = {int(v[1]): v for v in values}
                for label in sorted(label_to_row):
                    row = label_to_row[label]
                    sequence.append(DBItem('sample_frame_features', row[0], row[1]))
                return sequence

            # 3. Fallback: use fid order as sequence
            for v in sorted(values, key=lambda x: x[0]):
                sequence.append(DBItem('sample_frame_features', v[0], v[1]))
            return sequence

    except Exception as ex:
        sequence = []
        raise ex

    return sequence
