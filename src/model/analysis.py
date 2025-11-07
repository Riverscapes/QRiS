import json
import sqlite3
from typing import Dict

from .db_item_spatial import DBItemSpatial
from .sample_frame import SampleFrame
from .analysis_metric import AnalysisMetric, store_analysis_metrics

ANALYSIS_MACHINE_CODE = 'ANALYSIS'
default_units = {'distance': 'meters', 'area': 'square meters', 'ratio': 'ratio', 'count': 'count'}

class Analysis(DBItemSpatial):

    def __init__(self, id: int, name: str, description: str, sample_frame: SampleFrame, metadata: dict = None):
        super().__init__('analyses', id, name, sample_frame.fc_name, 'sample_frame_id', 'Polygon')
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
                self.create_spatial_view(curs)
                conn.commit()

                self.name = name
                self.description = description
                self.analysis_metrics = analysis_metrics
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise Exception(f"Error updating analysis {self.id}: {ex}") from ex
            

    def create_spatial_view(self, curs: sqlite3.Cursor) -> None:
        """Create a spatial view of the Analysis features."""
        # prepare sql string for each metric
        sql_metric = ", ".join(
            [f'CASE WHEN metric_id = {metric_id} THEN (CASE WHEN is_manual = 1 THEN manual_value ELSE automated_value END) END AS "{analysis_metric.metric.name}"' for metric_id, analysis_metric in self.analysis_metrics.items()])
        sql = f"""CREATE VIEW {self.view_name} AS SELECT * FROM sample_frame_features JOIN (SELECT sample_frame_feature_id, {sql_metric} FROM metric_values JOIN metrics ON metric_values.metric_id == metrics.id WHERE metric_values.analysis_id = {self.id} GROUP BY sample_frame_feature_id) AS x ON sample_frame_features.fid = x.sample_frame_feature_id"""
        if sql_metric == '':
            sql = f"CREATE VIEW {self.view_name} AS SELECT * FROM sample_frame_features WHERE sample_frame_id == {self.sample_frame.id}"
        # check if the view already exists, if so, delete it
        if self.check_spatial_view_exists(curs):
            curs.execute(f"DROP VIEW {self.view_name}")
            curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = '{self.view_name}'")
            curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = '{self.view_name}'")
        curs.execute(sql)
        # add view to geopackage
        sql = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id) VALUES (?, ?, ?, ?, ?)"
        curs.execute(sql, [self.view_name, "features", self.view_name, "", self.epsg])
        sql = (
            "INSERT INTO gpkg_geometry_columns "
            "(table_name, column_name, geometry_type_name, srs_id, z, m) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        curs.execute(sql, [self.view_name, 'geom', self.geom_type.upper(), self.epsg, 0, 0])


def load_analyses(curs: sqlite3.Cursor, sample_frames: dict, metrics: dict) -> Dict[int, Analysis] :

    curs.execute('SELECT * FROM analyses')
    analyses = {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        sample_frames[row['sample_frame_id']],
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

    analysis = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, sample_frame_id, metadata) VALUES (?, ?, ?, ?)', [
                name, description if description is not None and len(description) > 0 else None, sample_frame.id, metadata_str])
            analysis_id = curs.lastrowid
            analysis = Analysis(analysis_id, name, description, sample_frame, metadata=metadata)
            store_analysis_metrics(curs, analysis_id, analysis_metrics)
            analysis.analysis_metrics = analysis_metrics
            analysis.create_spatial_view(curs)
            conn.commit()
        except Exception as ex:
            conn.rollback()
            raise Exception(f"Error inserting analysis {name}: {ex}") from ex

    return analysis
