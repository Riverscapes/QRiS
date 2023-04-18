import os
import sqlite3

from qgis.core import QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext

from .analysis import Analysis, load_analyses
from .mask import Mask, load_masks
from .layer import Layer, load_layers, load_non_method_layers
from .method import Method, load as load_methods
from .protocol import Protocol, load as load_protocols
from .raster import Raster, load_rasters
from .event import Event, load as load_events
from .metric import Metric, load_metrics
from .pour_point import PourPoint, load_pour_points
from .scratch_vector import ScratchVector, load_scratch_vectors
from .stream_gage import StreamGage, load_stream_gages
from .profile import Profile, load_profiles
from .cross_sections import CrossSections, load_cross_sections
from .units import load_units
from .db_item import DBItem, dict_factory, load_lookup_table

from ..QRiS.path_utilities import parse_posix_path

PROJECT_MACHINE_CODE = 'Project'

# all spatial layers
# feature class, layer name, geometry
project_layers = [
    ('aoi_features', 'AOI Features', 'Polygon'),
    ('mask_features', 'Mask Features', 'Polygon'),
    ('dam_crests', 'Dam Crests', 'Linestring'),
    ('dams', 'Dam Points', 'Point'),
    ('jams', 'Jam Points', 'Point'),
    ('thalwegs', 'Thalwegs', 'Linestring'),
    ('active_extents', 'Active Extents', 'Polygon'),
    ('centerlines', 'Centerlines', 'Linestring'),
    ('inundation_extents', 'Inundation Extents', 'Polygon'),
    ('valley_bottoms', 'Valley Bottoms', 'Polygon'),
    ('junctions', 'Junctions', 'Point'),
    ('geomorphic_unit_extents', 'Geomorphic Unit Extents', 'Polygon'),
    ('geomorphic_units', 'Geomorphic Unit Points', 'Point'),
    ('geomorphic_units_tier3', 'Tier 3 Geomorphic Units', 'Point'),
    ('cem_phases', 'Channel Evolution Model Stages', 'Polygon'),
    ('vegetation_extents', 'Riparian Vegetation', 'Polygon'),
    ('floodplain_accessibilities', 'Floodplain Accessibility', 'Polygon'),
    ('brat_vegetation', 'BRAT Vegetation', 'Polygon'),
    ('zoi', 'Zones of Influence', 'Polygon'),
    ('complexes', 'Complexes', 'Polygon'),
    ('structure_points', 'Structure Points', 'Point'),
    ('structure_lines', 'Structure Lines', 'Linestring'),
    ('channel_unit_points', 'Channel Unit Points', 'Point'),
    ('channel_unit_polygons', 'Channel Unit Polygons', 'Polygon'),
    ('brat_cis', 'BRAT CIS', 'Point'),
    ('brat_cis_reaches', 'BRAT CIS Reaches', 'Linestring'),
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point'),
    ('profile_centerlines', 'Centerlines', 'Linestring'),
    ('profile_features', 'Profiles', 'Linestring'),
    ('cross_section_features', 'Cross Sections', 'Linestring')
]


class Project(DBItem):

    def __init__(self, project_file: str):
        super().__init__('projects', 1, 'Placeholder')

        self.project_file = parse_posix_path(project_file)
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            curs.execute('SELECT id, name, description, map_guid FROM projects LIMIT 1')
            project_row = curs.fetchone()
            self.name = project_row['name']
            self.id = project_row['id']
            self.description = project_row['description']
            self.map_guid = project_row['map_guid']

            self.lookup_tables = {table: load_lookup_table(curs, table) for table in [
                'lkp_mask_types',
                'lkp_platform',
                'lkp_event_types',
                'lkp_design_status',
                'lkp_raster_types',
                'lkp_scratch_vector_types',
                'lkp_representation',
                'lkp_units'
            ]}

            self.masks = load_masks(curs, self.lookup_tables['lkp_mask_types'])
            self.layers = load_layers(curs)
            self.non_method_layers = load_non_method_layers(curs)
            self.methods = load_methods(curs, self.layers)
            self.protocols = load_protocols(curs, self.methods)
            self.rasters = load_rasters(curs)
            self.scratch_vectors = load_scratch_vectors(curs, self.project_file)
            self.events = load_events(curs, self.protocols, self.methods, self.layers, self.lookup_tables, self.surface_rasters())
            self.metrics = load_metrics(curs)
            self.analyses = load_analyses(curs, self.masks, self.metrics)
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
        else:
            raise Exception('Attempting to remove unhandled database type from project')

    # def basemaps(self) -> dict:
    #     """ Returns a dictionary of just those rasters that are basemaps"""

    #     return {id: raster for id, raster in self.rasters.items() if raster.raster_type_id == RASTER_TYPE_BASEMAP}

    def scratch_rasters(self) -> dict:
        """ Returns a dictionary of all project rasters EXCEPT basemaps"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is True}

    def surface_rasters(self) -> dict:
        """ Returns a dictionary of all project surface rasters"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is False}


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
                except Exception as ex:
                    conn.rollback()
                    raise ex
                    # raise Exception('Error applying migration from file {}'.format(os.path.basename(migration_path)), inner=ex)

        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex
