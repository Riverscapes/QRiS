import sqlite3
import json

from .db_item import DBItem
from ..gp.analysis_metrics import analysis_metric_unit_type


METRIC_SCHEMA = './qris_metrics.schema.json'

default_units = {'distance': 'meters', 'area': 'square meters', 'ratio': 'ratio', 'count': 'count'}

class Metric(DBItem):

    def __init__(self, id: int, name: str, machine_name:str, description: str, default_level_id: int, metric_function: str, metric_params: str, default_unit_id: int = None, definition_url: str = None, metadata: dict = None):
        super().__init__('metrics', id, name)
        self.machine_name = machine_name
        self.description = description
        self.default_level_id = default_level_id
        self.default_unit_id = default_unit_id
        self.metric_function = metric_function
        self.metric_params = metric_params
        self.icon = 'calculate'
        self.definition_url = definition_url
        self.metadata = metadata
        # This is the base unit as defined in the metric calculation function
        self.unit_type = analysis_metric_unit_type.get(self.metric_function, None)
        self.base_unit = default_units.get(self.unit_type, None)
        self.normalized = True if metric_params is not None and 'normalization' in metric_params else False
        if self.normalized:
            self.base_unit = 'meters'
            if self.unit_type == 'distance':
                self.unit_type = 'ratio'
        self.tolerance = self.metadata['tolerance'] if self.metadata and 'tolerance' in self.metadata else None  # no tolerance = no testing for tolerance
        self.min_value = self.metadata['min_value'] if self.metadata and 'min_value' in self.metadata else None
        self.max_value = self.metadata['max_value'] if self.metadata and 'max_value' in self.metadata else None
        self.precision = self.metadata['precision'] if self.metadata and 'precision' in self.metadata else None  # No precision = full float value


def load_metrics(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM calculations')
    metric_functions = {row['id']: row['metric_function'] for row in curs.fetchall()}

    curs.execute('SELECT * FROM metrics')
    return {row['id']: Metric(
        row['id'],
        row['name'],
        row['machine_name'],
        row['description'],
        row['default_level_id'],
        metric_functions.get(row['calculation_id'], None),
        json.loads(row['metric_params']) if row['metric_params'] else None,
        row['unit_id'],
        row['definition_url'],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}

def insert_metric(db_path: str, name: str, machine_name: str, description: str, metric_level, metric_function, metric_params, default_unit, definition_url, metadata=None) -> Metric:

    metric = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None
    metric_params_str = json.dumps(metric_params) if metric_params is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            # get the metric level id
            curs.execute('SELECT id FROM metric_levels WHERE name = ?', [metric_level])
            metric_level_ids = curs.fetchone()
            if metric_level_ids is None:
                raise ValueError(f"Metric Level type '{metric_level}' not found in database.")
            metric_level_id = metric_level_ids[0]
            # get the calculation id
            curs.execute('SELECT id FROM calculations WHERE metric_function = ?', [metric_function])
            calculation_ids = curs.fetchone()
            if calculation_ids is None:
                raise ValueError(f"Calculation '{metric_function}' not found in database.")
            calculation_id = calculation_ids[0]
            # get the unit id
            if default_unit is not None and default_unit != '':
                curs.execute('SELECT id FROM lkp_units WHERE name = ?', [default_unit])
                unit_ids = curs.fetchone()
                if unit_ids is None:
                    raise ValueError(f"Unit '{default_unit}' not found in database.")
                unit_id = unit_ids[0]
            else:
                unit_id = None

            curs.execute('INSERT INTO metrics (name, machine_name, description, default_level_id, calculation_id, metric_params, unit_id, definition_url, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [name, machine_name, description, metric_level_id, calculation_id, metric_params_str, unit_id, definition_url, metadata_str])
            id = curs.lastrowid
            metric = Metric(id, name, machine_name, description, metric_level_id, metric_function, metric_params, unit_id, definition_url, metadata)
            conn.commit()

        except Exception as ex:
            metric = None
            conn.rollback()
            raise ex

    return id, metric