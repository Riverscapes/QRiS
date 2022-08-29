from email.mime import base
import sqlite3
from .db_item import DBItem
from .basemap import Raster
from .mask import Mask

ANALYSIS_MACHINE_CODE = 'ANALYSIS'


class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str, mask: Mask):
        super().__init__('analyses', id, name)
        self.description = description
        self.icon = 'analysis'
        self.mask = mask
        self.metrics = None

    def update(self, db_path: str, name: str, description: str, active_metrics: dict) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ? WHERE id = ?', [name, description, self.id])

                store_analysis_metrics(curs, self.id, active_metrics)

                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_analyses(curs: sqlite3.Cursor, masks: dict, metrics: dict) -> dict:

    curs.execute('SELECT * FROM analyses')
    analyses = {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        masks[row['mask_id']]
    ) for row in curs.fetchall()}

    for analysis_id, analysis in analyses.items():
        curs.execute('SELECT * FROM analysis_metrics WHERE analysis_id = ?', [analysis_id])
        analysis.metrics = {row['metric_id']: metrics[row['metric_id']] for row in curs.fetchall()}

    return analyses


def insert_analysis(db_path: str, name: str, description: str, mask: Mask, active_metrics: dict) -> Analysis:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, mask_id) VALUES (?, ?, ?)', [
                name, description, mask.id])
            analysis_id = curs.lastrowid
            result = Analysis(analysis_id, name, description, mask)

            store_analysis_metrics(curs, analysis_id, active_metrics)

            conn.commit()
        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result


def store_analysis_metrics(curs: sqlite3.Cursor, analysis_id: int, active_metrics: dict) -> None:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    # delete any metrics not present
    curs.execute('SELECT metric_id FROM analysis_metrics WHERE analysis_id = ?', [analysis_id])
    existing_metric_ids = [row['metric_id'] for row in curs.fetchall()]

    for metric_id in existing_metric_ids:
        if metric_id not in active_metrics:
            curs.execute('DELETE FROM analysis_metrics WHERE analyis_id = ? AND metric_id = ?', [analysis_id, metric_id])

    # Upsert to ensure all existing active metrics are stored
    curs.executemany("""INSERT INTO analysis_metrics (analysis_id, metric_id, level_id) VALUES (?, ?, ?)
                ON CONFLICT (analysis_id, metric_id) DO UPDATE SET level_id = excluded.level_id""",
                     [(analysis_id, metric_id, level_id) for metric_id, level_id in active_metrics.items()])
