import os
import sqlite3

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


def apply_db_migrations(db_path: str):

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    curs = conn.cursor()

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
                    raise Exception('Error applying migration from file {}'.format(os.path.basename(migration_path)), inner=ex)

        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex
