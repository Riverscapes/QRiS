import sqlite3
import json

from .db_item import DBItem


class Metric(DBItem):

    def __init__(self, id: int, name: str, description: str, default_level_id: int, metric_function: str, metric_params: str, default_unit_id: int = None, metadata: dict = None):
        super().__init__('metrics', id, name)
        self.description = description
        self.default_level_id = default_level_id
        self.default_unit_id = default_unit_id
        self.metric_function = metric_function
        self.metric_params = metric_params
        self.icon = 'calculate'
        self.metadata = metadata

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
        row['description'],
        row['default_level_id'],
        metric_functions.get(row['calculation_id'], None),
        json.loads(row['metric_params']) if row['metric_params'] else None,
        row['unit_id'],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}
