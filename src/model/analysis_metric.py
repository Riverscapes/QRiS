import sqlite3
from .metric import Metric


class AnalysisMetric():
    """ Convenience class for tracking metrics used in an
    analysis. Simply tracks a metric and the level (metric or indicator)
    at which it is used"""

    def __init__(self, metric: Metric, level_id: int):
        self.metric = metric
        self.level_id = level_id


def store_analysis_metrics(curs: sqlite3.Cursor, analysis_id: int, analysis_metrics: dict) -> None:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    # delete any metrics not present
    curs.execute('SELECT metric_id FROM analysis_metrics WHERE analysis_id = ?', [analysis_id])
    existing_metric_ids = [row[0] for row in curs.fetchall()]

    for metric_id in existing_metric_ids:
        if metric_id not in analysis_metrics:
            curs.execute('DELETE FROM analysis_metrics WHERE analysis_id = ? AND metric_id = ?', [analysis_id, metric_id])

    # Upsert to ensure all existing active metrics are stored
    curs.executemany("""INSERT INTO analysis_metrics (analysis_id, metric_id, level_id) VALUES (?, ?, ?)
                ON CONFLICT (analysis_id, metric_id) DO UPDATE SET level_id = excluded.level_id""",
                     [(analysis_id, metric_id, analysis_metric.level_id) for metric_id, analysis_metric in analysis_metrics.items()])
