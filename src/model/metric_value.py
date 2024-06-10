import typing
import sqlite3
import json

from .metric import Metric
from .event import Event
from .analysis import Analysis
from .db_item import dict_factory
from ..lib.unit_conversion import convert_units

class MetricValue():

    def __init__(self, metric: Metric, manual_value: float, automated_value: float, is_manual: bool, uncertainty: float, description: str, unit_id: int, metadata: dict):

        self.metric = metric
        self.manual_value = manual_value
        self.automated_value = automated_value
        self.is_manual = is_manual
        self.uncertainty = uncertainty
        self.unit_id = unit_id
        self.metadata = metadata
        self.description = description
            
    def current_value(self, display_unit: str = None):
        value = self.manual_value if self.is_manual else self.automated_value
        if display_unit is not None:
            value = convert_units(value, self.metric.base_unit, display_unit, invert=self.metric.normalized)
        return value
    
    def current_value_as_string(self, display_unit: str = None):
        value = self.current_value(display_unit)
        if isinstance(value, float) and self.metric.precision is not None:
            return f'{value: .{self.metric.precision}f}'
        return str(value)
    
    def uncertainty_as_string(self):
        if self.uncertainty is None:
            return ''
        if self.is_manual:
            return print_uncertanty(self.uncertainty)
        return ''

    def save(self, db_path: str, analysis: Analysis, event: Event, sample_frame_feature_id: int, unit_id: int = None):

        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            try:
                curs.execute("""INSERT INTO metric_values (
                        analysis_id
                        , event_id
                        , sample_frame_feature_id
                        , metric_id
                        , manual_value
                        , automated_value
                        , is_manual
                        , uncertainty
                        , unit_id
                        , metadata
                        , description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (analysis_id, event_id, sample_frame_feature_id, metric_id) DO UPDATE SET
                        manual_value = excluded.manual_value
                        , automated_value = excluded.automated_value
                        , is_manual = excluded.is_manual
                        , uncertainty = excluded.uncertainty
                        , metadata = excluded.metadata
                        , description = excluded.description""", [
                    analysis.id,
                    event.id,
                    sample_frame_feature_id,
                    self.metric.id,
                    self.manual_value,
                    self.automated_value,
                    self.is_manual,
                    json.dumps(self.uncertainty),
                    unit_id,
                    json.dumps(self.metadata) if self.metadata is not None and len(self.metadata) > 0 else None,
                    self.description
                ])
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise ex


def load_metric_values(db_path: str, analysis: Analysis, event: Event, sample_frame_feature_id: int, metrics: dict) -> typing.Dict[int, MetricValue]:
    """ returns metric_id keyed to analysis_metric_value
    """

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute('SELECT * FROM metric_values WHERE (analysis_id = ?) AND (event_id = ?) AND (sample_frame_feature_id = ?)',
                     [analysis.id, event.id, sample_frame_feature_id])
        return {
            row['metric_id']: MetricValue(
                metrics[row['metric_id']],
                row['manual_value'],
                row['automated_value'],
                row['is_manual'],
                json.loads(row['uncertainty']) if row['uncertainty'] is not None else None,
                row['description'],
                row['unit_id'],
                json.loads(row['metadata']) if row['metadata'] is not None else {}
            )
            for row in curs.fetchall()
        }


def print_uncertanty(uncertainty: dict):

    if uncertainty is None:
        return None
    elif uncertainty.get('Plus/Minus') is not None:
        return f"+/- {uncertainty['Plus/Minus']:.2f}"
    elif uncertainty.get('Percent') is not None:
        return f"+/- {uncertainty['Percent']:.2f}%"
    elif uncertainty.get('Min/Max') is not None:
        return f"Range: {uncertainty['Min/Max'][0]:.2f} - {uncertainty['Min/Max'][1]:.2f}"
    else:
        return 'Undefined'
