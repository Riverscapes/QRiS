import json
import sqlite3

from .db_item import DBItem
from .raster import Raster
from .sample_frame import SampleFrame
from .analysis_metric import AnalysisMetric, store_analysis_metrics

ANALYSIS_MACHINE_CODE = 'ANALYSIS'
default_units = {'distance': 'meters', 'area': 'square meters', 'ratio': 'ratio', 'count': 'count'}

class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str, sample_frame: SampleFrame, metadata: dict = None):
        super().__init__('analyses', id, name)
        self.description = description
        self.icon = 'analysis'
        self.sample_frame = sample_frame
        self.analysis_metrics = None
        self.metadata = metadata
        self.profile = metadata.get('centerline', None) if metadata is not None else None # really just the profile id
        self.dem = metadata.get('dem', None) if metadata is not None else None
        self.units = metadata.get('units', default_units) if metadata is not None else default_units
    
    def update(self, db_path: str, name: str, description: str, analysis_metrics: dict, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        self.metadata['units'] = self.units
        metadata_str = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])

                store_analysis_metrics(curs, self.id, analysis_metrics)

                conn.commit()

                self.name = name
                self.description = description
                self.analysis_metrics = analysis_metrics
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex


def load_analyses(curs: sqlite3.Cursor, sample_frames: dict, metrics: dict) -> dict:

    curs.execute('SELECT * FROM analyses')
    analyses = {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        sample_frames[row['mask_id']],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}

    for analysis_id, analysis in analyses.items():
        curs.execute('SELECT * FROM analysis_metrics WHERE analysis_id = ?', [analysis_id])
        analysis.analysis_metrics = {row['metric_id']: AnalysisMetric(metrics[row['metric_id']], row['level_id']) for row in curs.fetchall()}

    return analyses


def insert_analysis(db_path: str, name: str, description: str, sample_frame: SampleFrame, analysis_metrics: dict, metadata: dict=None) -> Analysis:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    metadata_str = json.dumps(metadata) if metadata is not None else None

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, mask_id, metadata) VALUES (?, ?, ?, ?)', [
                name, description if description is not None and len(description) > 0 else None, sample_frame.id, metadata_str])
            analysis_id = curs.lastrowid
            analysis = Analysis(analysis_id, name, description, sample_frame, metadata=metadata)

            store_analysis_metrics(curs, analysis_id, analysis_metrics)
            analysis.analysis_metrics = analysis_metrics

            conn.commit()
        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return analysis
