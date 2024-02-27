import os
import json
import sqlite3

from qgis.core import Qgis, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsMessageLog

from .analysis import Analysis, load_analyses
from .mask import Mask, load_masks
from .sample_frame import SampleFrame, load_sample_frames
from .layer import Layer, load_layers, load_non_method_layers
from .method import Method, load as load_methods
from .protocol import Protocol, load as load_protocols
from .raster import Raster, load_rasters
from .event import Event, load as load_events
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
    ('aoi_features', 'AOI Features', 'Polygon'),
    ('mask_features', 'Mask Features', 'Polygon'),
    ('sample_frame_features', 'Sample Frame Features', 'Polygon'),
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point'),
    ('profile_centerlines', 'Centerlines', 'Linestring'),
    ('profile_features', 'Profiles', 'Linestring'),
    ('cross_section_features', 'Cross Sections', 'Linestring'),
    ('dce_points', 'DCE Points', 'Point'),
    ('dce_lines', 'DCE Lines', 'Linestring'),
    ('dce_polygons', 'DCE Polygons', 'Polygon')
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
            self.lookup_values = self.get_lookups()

            # get list of lookup tables from layers where is_lookup = 1
            lkp_tables = [row['fc_name'] for row in curs.execute('SELECT DISTINCT fc_name FROM layers WHERE is_lookup = 1').fetchall()]
            # TODO clean up the schema to avoid this hack
            # for table in ['lkp_brat_combined_cis', 'lkp_brat_vegetation_cis', 'lkp_units']:
            #     lkp_tables.remove(table)
            lkp_tables.append('lkp_event_types')
            lkp_tables.append('lkp_raster_types')
            lkp_tables.append('lkp_scratch_vector_types')
            self.lookup_tables = {table: load_lookup_table(curs, table) for table in lkp_tables}

            self.masks = load_masks(curs, self.lookup_tables['lkp_mask_types'])
            self.aois = load_masks(curs, self.lookup_tables['lkp_mask_types'])
            self.sample_frames = load_sample_frames(curs)
            self.layers = load_layers(curs)
            self.non_method_layers = load_non_method_layers(curs)
            self.methods = load_methods(curs, self.layers)
            self.protocols = load_protocols(curs, self.methods)
            self.rasters = load_rasters(curs)
            self.scratch_vectors = load_scratch_vectors(curs, self.project_file)
            self.events = load_events(curs, self.protocols, self.methods, self.layers, self.lookup_tables, self.surface_rasters())
            self.metrics = load_metrics(curs)
            self.analyses = load_analyses(curs, self.sample_frames, self.metrics)
            self.pour_points = load_pour_points(curs)
            self.stream_gages = load_stream_gages(curs)
            self.profiles = load_profiles(curs)
            self.cross_sections = load_cross_sections(curs)

            self.units = load_units(curs)

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

        if isinstance(db_item, Mask):
            self.masks.pop(db_item.id)
        elif isinstance(db_item, SampleFrame):
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

    def get_lookups(self) -> dict:
        # load and parse all of the lookups from the lookup_list_values table if it exists
        lookups = {}
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute('SELECT * FROM lookup_list_values')
            for row in curs.fetchall():
                if row['list_name'] not in lookups:
                    lookups[row['list_name']] = []
                lookups[row['list_name']].append(row['list_value'])
        return lookups

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

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    curs = conn.cursor()

    existing_layers = [layer[0] for layer in curs.execute('SELECT table_name, data_type FROM gpkg_contents WHERE data_type = "features"').fetchall()]

    for fc_name, layer_name, geometry_type in project_layers:
        if fc_name not in existing_layers:
            features_path = '{}|layername={}'.format(db_path, layer_name)
            create_geopackage_table(geometry_type, fc_name, db_path, features_path, None)
            QgsMessageLog.logMessage(f'Appling QRiS Database Migrations: create feature class {layer_name}', 'QRiS', Qgis.Info)

    try:
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'db', 'migrations')
        for migration_file in os.listdir(migrations_dir):
            curs.execute('SELECT * FROM migrations WHERE file_name LIKE ?', [migration_file])
            migration_row = curs.fetchone()
            if migration_row is None:
                try:
                    migration_path = os.path.join(migrations_dir, migration_file)
                    with open(migration_path, 'r') as f:
                        sql_commands = f.read()
                        curs.executescript(sql_commands)
                    curs.execute('INSERT INTO migrations (file_name) VALUES (?)', [migration_file])
                    QgsMessageLog.logMessage(f'Appling QRiS Database Migrations: {migration_file}', 'QRiS', Qgis.Info)
                except Exception as ex:
                    conn.rollback()
                    raise ex
                    # raise Exception('Error applying migration from file {}'.format(os.path.basename(migration_path)), inner=ex)

        conn.commit()
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

