import typing
import sqlite3
import json
from .metric import Metric
from .event import Event
from .analysis import Analysis


class MetricValue():

    def __init__(self, metric: Metric, manual_value: float, automated_value: float, is_manual: bool, uncertainty: float, description: str, metadata: dict):

        self.metric = metric
        self.manual_value = manual_value
        self.automated_value = automated_value
        self.is_manual = is_manual
        self.uncertainty = uncertainty

        self.metadata = metadata
        self.description = description

    def save(self, db_path: str, analysis: Analysis, event: Event, mask_feature_id: int):

        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            try:
                curs.execute("""INSERT INTO metric_values (
                        analysis_id
                        , event_id
                        , mask_feature_id
                        , metric_id
                        , manual_value
                        , automated_value
                        , is_manual
                        , uncertainty
                        , metadata
                        , description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (analysis_id, event_id, mask_feature_id, metric_id) DO UPDATE SET
                        manual_value = excluded.manual_value
                        , automated_value = excluded.automated_value
                        , is_manual = excluded.is_manual
                        , uncertainty = excluded.uncertainty
                        , metadata = excluded.metadata
                        , description = excluded.description""", [
                    analysis.id,
                    event.id,
                    mask_feature_id,
                    self.metric.id,
                    self.manual_value,
                    self.automated_value,
                    self.is_manual,
                    self.uncertainty,
                    json.dumps(self.metadata) if self.metadata is not None and len(self.metadata) > 0 else None
                ])
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise ex


def load_metric_values(db_path: str, analysis: Analysis, event: Event, mask_feature_id: int, metrics: dict) -> typing.Dict[int, MetricValue]:
    """ returns metric_id keyed to analysis_metric_value
    """

    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute('SELECT * FROM metric_values WHERE (analysis_id = ?) AND (event_id = ?) AND (mask_feature_id = ?)',
                     [analysis.id, event.id, mask_feature_id])
        return {
            row['metric_id']: MetricValue(
                metrics[row['metric_id']],
                row['manual_value'],
                row['automated_value'],
                row['is_manual'],
                row['uncertainty'],
                row['description'],
                json.loads(row['metadata']) if row.IsDBNull(row) else {}
            )
            for row in curs.fetchall()
        }
