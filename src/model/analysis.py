from email.mime import base
import sqlite3
from .db_item import DBItem
from .raster import Raster
from .mask import Mask
from .analysis_metric import AnalysisMetric, store_analysis_metrics

ANALYSIS_MACHINE_CODE = 'ANALYSIS'


class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str, mask: Mask):
        super().__init__('analyses', id, name)
        self.description = description
        self.icon = 'analysis'
        self.mask = mask
        self.analysis_metrics = None

    def update(self, db_path: str, name: str, description: str, analysis_metrics: dict) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ? WHERE id = ?', [name, description, self.id])

                store_analysis_metrics(curs, self.id, analysis_metrics)

                conn.commit()

                self.name = name
                self.description = description
                self.analysis_metrics = analysis_metrics

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
        analysis.analysis_metrics = {row['metric_id']: AnalysisMetric(metrics[row['metric_id']], row['level_id']) for row in curs.fetchall()}

    return analyses


def insert_analysis(db_path: str, name: str, description: str, mask: Mask, analysis_metrics: dict) -> Analysis:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, mask_id) VALUES (?, ?, ?)', [
                name, description if description is not None and len(description) > 0 else None, mask.id])
            analysis_id = curs.lastrowid
            analysis = Analysis(analysis_id, name, description, mask)

            store_analysis_metrics(curs, analysis_id, analysis_metrics)
            analysis.analysis_metrics = analysis_metrics

            conn.commit()
        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return analysis
