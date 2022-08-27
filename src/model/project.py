import os
import sqlite3

from .analysis import load_analyses
from .mask import Mask, load_masks
from .layer import Layer, load_layers
from .protocol import Protocol, load as load_protocols
from .basemap import Raster, load_rasters, RASTER_TYPE_BASEMAP
from .event import Event, load as load_events
from .metric import Metric, load_metrics
from .pour_point import PourPoint, load_pour_points

from .db_item import DBItem, dict_factory, load_lookup_table

from pathlib import Path, PurePosixPath

PROJECT_MACHINE_CODE = 'Project'


class Project(DBItem):

    def __init__(self, project_file: str):
        super().__init__('projects', 1, 'Placeholder')

        self.project_file = project_file
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            curs.execute('SELECT id, name, description FROM projects LIMIT 1')
            project_row = curs.fetchone()
            self.name = project_row['name']
            self.id = project_row['id']
            self.description = project_row['description']

            self.lookup_tables = {table: load_lookup_table(curs, table) for table in [
                'lkp_mask_types',
                'lkp_platform',
                'lkp_event_types',
                'lkp_design_status',
                'lkp_raster_types'
            ]}

            self.masks = load_masks(curs, self.lookup_tables['lkp_mask_types'])
            self.layers = load_layers(curs)
            self.protocols = load_protocols(curs, self.layers)
            self.rasters = load_rasters(curs)
            self.events = load_events(curs, self.protocols, self.lookup_tables, self.basemaps())
            self.analyses = load_analyses(curs, self.masks)
            self.pour_points = load_pour_points(curs)
            self.metrics = load_metrics(curs)

    def get_relative_path(self, absolute_path: str) -> str:
        return parse_posix_path(os.path.relpath(absolute_path, os.path.dirname(self.project_file)))

    def get_absolute_path(self, relative_path: str) -> str:
        return os.path.join(os.path.dirname(self.project_file), relative_path)

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
        else:
            raise Exception('Attempting to remove unhandled database type from project')

    def basemaps(self) -> dict:
        """ Returns a dictionary of just those rasters that are basemaps"""

        return {id: raster for id, raster in self.rasters.items() if raster.raster_type_id == RASTER_TYPE_BASEMAP}

    def scratch_rasters(self) -> dict:
        """ Returns a dictionary of all project rasters EXCEPT basemaps"""

        return {id: raster for id, raster in self.rasters.items() if raster.raster_type_id != RASTER_TYPE_BASEMAP}


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


def parse_posix_path(path: str) -> str:
    """This method returns a posix path no matter if you pass it a windows or a linux path

    Args:
        path ([type]): [description]
    """
    new_path = PurePosixPath(path.replace('\\', '/'))
    return str(new_path)
