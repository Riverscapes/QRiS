import os
import json
import sqlite3
from sqlite3 import Connection

from qgis.core import Qgis, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsMessageLog
from qgis.utils import spatialite_connect

from .analysis import Analysis, load_analyses
from .sample_frame import SampleFrame, load_sample_frames
from .layer import Layer, load_layers
from .protocol import Protocol, load as load_protocols
from .raster import Raster, load_rasters
from .event import Event, load as load_events
from .planning_container import PlanningContainer, load as load_planning_containers
from .event_layer import EventLayer
from .metric import Metric, load_metrics
from .pour_point import PourPoint, load_pour_points
from .scratch_vector import ScratchVector, load_scratch_vectors
from .stream_gage import StreamGage, load_stream_gages
from .profile import Profile, load_profiles
from .cross_sections import CrossSections, load_cross_sections
from .units import load_units
from .db_item import DBItem, dict_factory, load_lookup_table

from ..QRiS.path_utilities import parse_posix_path
from typing import Generator

PROJECT_MACHINE_CODE = 'Project'

# all spatial layers
# feature class, layer name, geometry
project_layers = [
    ('aoi_features', 'AOI Features', 'Polygon'), # Keep so the migration scripts can run
    ('mask_features', 'Mask Features', 'Polygon'), # Keep so the migration scripts can run
    ('sample_frame_features', 'Sample Frame Features', 'Polygon'),
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point'),
    ('profile_centerlines', 'Centerlines', 'Linestring'),
    ('profile_features', 'Profiles', 'Linestring'),
    ('cross_section_features', 'Cross Sections', 'Linestring'),
    ('valley_bottom_features', 'Valley Bottoms', 'Polygon'), # Keep so the migration scripts can run
    ('dce_points', 'DCE Points', 'Point'),
    ('dce_lines', 'DCE Lines', 'Linestring'),
    ('dce_polygons', 'DCE Polygons', 'Polygon')
]

# migrated layers not to be recreated
migrated_layers = [
    'aoi_features',
    'mask_features',
    'valley_bottom_features'
]

class Project(DBItem):

    def __init__(self, project_file: str):
        super().__init__('projects', 1, 'Placeholder')

        self.project_file = parse_posix_path(project_file)
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            curs.execute('SELECT id, name, description, map_guid, metadata FROM projects LIMIT 1')
            project_row = curs.fetchone()
            self.name = project_row['name']
            self.id = project_row['id']
            self.description = project_row['description']
            self.map_guid = project_row['map_guid']
            self.metadata = json.loads(project_row['metadata'] if project_row['metadata'] is not None else '{}')

            # get list of lookup tables
            lkp_tables = [row['name'] for row in curs.execute('SELECT DISTINCT name FROM lookups').fetchall()]
            self.lookup_tables = {table: load_lookup_table(curs, table) for table in lkp_tables}

            self.aois = load_sample_frames(curs, sample_frame_type=SampleFrame.AOI_SAMPLE_FRAME_TYPE)
            self.sample_frames = load_sample_frames(curs)
            self.layers = load_layers(curs)
            self.protocols = load_protocols(curs, self.layers)
            self.rasters = load_rasters(curs)
            self.scratch_vectors = load_scratch_vectors(curs, self.project_file)
            self.events = load_events(curs, self.protocols, None, self.layers, self.lookup_tables, self.rasters)
            self.planning_containers = load_planning_containers(curs, self.events)
            self.metrics = load_metrics(curs)
            self.pour_points = load_pour_points(curs)
            self.stream_gages = load_stream_gages(curs)
            self.profiles = load_profiles(curs)
            self.cross_sections = load_cross_sections(curs)
            self.valley_bottoms = load_sample_frames(curs, sample_frame_type=SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE)
            self.analyses = load_analyses(curs, self.analysis_masks(), self.metrics)

            self.units = load_units(curs)

    def analysis_masks(self) -> dict:
        masks = self.sample_frames.copy()
        masks.update(self.aois)
        masks.update(self.valley_bottoms)
        return masks

    def get_relative_path(self, absolute_path: str) -> str:
        return parse_posix_path(os.path.relpath(absolute_path, os.path.dirname(self.project_file)))

    def get_absolute_path(self, relative_path: str) -> str:
        return parse_posix_path(os.path.join(os.path.dirname(self.project_file), relative_path))

    def get_safe_file_name(self, raw_name: str, ext: str = None):
        name = raw_name.strip().replace(' ', '_').replace('__', '_')
        if ext is not None:
            name = name + ext
        return name

    def remove(self, db_item: DBItem):

        if isinstance(db_item, SampleFrame):
            if db_item.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                self.aois.pop(db_item.id)
            elif db_item.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                self.valley_bottoms.pop(db_item.id)
            else:
                self.sample_frames.pop(db_item.id)
        elif isinstance(db_item, Raster):
            self.rasters.pop(db_item.id)
        elif isinstance(db_item, Event):
            self.events.pop(db_item.id)
        elif isinstance(db_item, PourPoint):
            self.pour_points.pop(db_item.id)
        elif isinstance(db_item, Analysis):
            self.analyses.pop(db_item.id)
        elif isinstance(db_item, ScratchVector):
            self.scratch_vectors.pop(db_item.id)
        elif isinstance(db_item, Profile):
            self.profiles.pop(db_item.id)
        elif isinstance(db_item, CrossSections):
            self.cross_sections.pop(db_item.id)
        elif isinstance(db_item, EventLayer):
            event_layer_index = list(event_layer.id for event_layer in self.events[db_item.event_id].event_layers).index(db_item.id)
            self.events[db_item.event_id].event_layers.pop(event_layer_index)
        elif isinstance(db_item, PlanningContainer):
            self.planning_containers.pop(db_item.id)
        else:
            raise Exception('Attempting to remove unhandled database type from project')

    def update_metadata(self, metadata: dict = None):

        if metadata is not None:
            self.metadata.update(metadata)

        with sqlite3.connect(self.project_file) as conn:
            conn.execute('UPDATE projects SET metadata = ? WHERE id = ?', [json.dumps(self.metadata), self.id])

    def scratch_rasters(self) -> dict:
        """ Returns a dictionary of all project rasters EXCEPT basemaps"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is True}

    def surface_rasters(self) -> dict:
        """ Returns a dictionary of all project surface rasters"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is False}

    def get_vector_dbitems(self) -> Generator[DBItem, None, None]:

        # yield all vector dbitems
        for dbitem in self.aois.values():
            yield dbitem
        for dbitem in self.sample_frames.values():
            yield dbitem
        for dbitem in self.pour_points.values():
            yield dbitem
        for dbitem in self.stream_gages.values():
            yield dbitem
        for dbitem in self.profiles.values():
            yield dbitem
        for dbitem in self.cross_sections.values():
            yield dbitem
        for dbitem in self.scratch_vectors.values():
            yield dbitem
        for dbitem in self.valley_bottoms.values():
            yield dbitem
        # for dbitem in self.layers.values():
        #     yield dbitem

def create_geopackage_table(geometry_type: str, table_name: str, geopackage_path: str, full_path: str, field_tuple_list: list = None):
    """
        Creates tables in existing or new geopackages
        geometry_type (string):  NoGeometry, Polygon, Linestring, Point, etc...
        table_name (string): Name for the new table
        geopackage_path (string): full path to the geopackage i.e., dir/package.gpkg
        full_path (string): full path including the layer i.e., dir/package.gpkg|layername=layer
        field_tuple_list (list): a list of tuples as field name and QVariant field types i.e., [('my_field', QVarient.Double)]
        """
    memory_layer = QgsVectorLayer(geometry_type, "memory_layer", "memory")
    if field_tuple_list:
        fields = []
        for field_tuple in field_tuple_list:
            field = QgsField(field_tuple[0], field_tuple[1])
            fields.append(field)
        memory_layer.dataProvider().addAttributes(fields)
        memory_layer.updateFields()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = table_name
    options.driverName = 'GPKG'
    transform = QgsCoordinateTransformContext()
    if os.path.exists(geopackage_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormatV3(memory_layer, geopackage_path, transform, options)


def apply_db_migrations(db_path: str):

    conn: Connection = spatialite_connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.execute('SELECT EnableGpkgMode();')
    curs = conn.cursor()

    existing_layers = [layer[0] for layer in curs.execute('SELECT table_name, data_type FROM gpkg_contents WHERE data_type = "features"').fetchall()]
    existing_layers = existing_layers + migrated_layers

    for fc_name, layer_name, geometry_type in project_layers:
        if fc_name not in existing_layers:
            features_path = '{}|layername={}'.format(db_path, layer_name)
            create_geopackage_table(geometry_type, fc_name, db_path, features_path, None)
            QgsMessageLog.logMessage(f'Appling QRiS Database Migrations: create feature class {layer_name}', 'QRiS', Qgis.Info)

    try:
        # find any aoi or valley bottom views and update them to use the sample frame feature class
        curs.execute('SELECT name FROM sqlite_master WHERE type="view"')
        views = curs.fetchall()
        for view in views:
            view_name = view[0]
            if view_name.startswith('vw_aoi') or view_name.startswith('vw_valley_bottom'):
                # if the view has a mask_id column, update it to use the sample_frame_features feature class
                curs.execute(f'PRAGMA table_info({view_name})')
                columns = curs.fetchall()
                mask_column_name = 'mask_id' if view_name.startswith('vw_aoi') else 'valley_bottom_id'
                mask_id_column = next((column for column in columns if column[1] == mask_column_name), None)
                if mask_id_column is not None:
                    mask_id = curs.execute(f'SELECT {mask_column_name} FROM {view_name} LIMIT 1').fetchone()
                    if mask_id is not None:
                        conn.execute('BEGIN')
                        curs.execute(f'DROP VIEW IF EXISTS {view_name}')
                        curs.execute(f'CREATE VIEW {view_name} AS SELECT * FROM sample_frame_features WHERE sample_frame_id = {mask_id[0]}') 
                        QgsMessageLog.logMessage(f'Appling QRiS Database Migrations: updated view {view_name}', 'QRiS', Qgis.Info)
                        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex

    try:
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'db', 'migrations')
        migration_files = os.listdir(migrations_dir)
        sorted_migration_files = sorted(migration_files)
        for migration_file in sorted_migration_files:
            curs.execute('SELECT * FROM migrations WHERE file_name LIKE ?', [migration_file])
            migration_row = curs.fetchone()
            if migration_row is None:
                try:
                    migration_path = os.path.join(migrations_dir, migration_file)
                    QgsMessageLog.logMessage(f'Appling QRiS Database Migrations: {migration_file}', 'QRiS', Qgis.Info)
                    with open(migration_path, 'r') as f:
                        sql_commands = f.read()
                    conn.execute('BEGIN')
                    curs.executescript(sql_commands)
                    curs.execute('INSERT INTO migrations (file_name) VALUES (?)', [migration_file])
                    conn.commit()
                except Exception as ex:
                    conn.rollback()
                    raise ex
    except Exception as ex:
        conn.rollback()
        raise ex

def test_project(db_path):

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()

        # cherck if the project table exists
        curs.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="projects"')
        if curs.fetchone() is None:
            raise Exception(f'The file {db_path} is not a QRiS project file.')

