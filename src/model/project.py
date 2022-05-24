import os
import sqlite3

from .mask import Mask, load_masks
from .layer import Layer, load_layers
from .method import Method, load_methods
from .basemap import Basemap, load_basemaps
from .assessment import Assessment, load_assessments

from .db_item import dict_factory, load_lookup_table

from pathlib import Path, PurePosixPath

from qgis import processing


class Project():

    def __init__(self, project_file: str):

        self.project_file = project_file
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            curs.execute('SELECT fid, name FROM projects LIMIT 1')
            project_row = curs.fetchone()
            self.name = project_row['name']
            self.id = project_row['fid']

            self.lookup_tables = {
                'mask_types': load_lookup_table(curs, 'lkp_mask_types')
            }

            self.masks = load_masks(curs, self.lookup_tables['mask_types'])
            self.layers = load_layers(curs)
            self.methods = load_methods(curs)
            self.basemaps = load_basemaps(curs)
            self.assessments = load_assessments(curs, self.methods, self.basemaps)

    def get_relative_path(self, absolute_path: str) -> str:
        return parse_posix_path(os.path.relpath(absolute_path, os.path.dirname(self.project_file)))

    def get_absolute_path(self, relative_path: str) -> str:
        return os.path.join(self.project_file, relative_path)

    def copy_raster_to_project(self, source_path: str, mask_path, relative_path: str) -> str:

        project_path = self.get_absolute_path(relative_path)

        args = {
            'INPUT': source_path,
            'OUTPUT': project_path
        }

        if mask_path is not None:
            args['OVERLAY'] = mask_path

        # output_info = processing.run('native:clip', args)

        # ds = gdal.Open(self.txtOriginalRasterPath.text())
        # driver = gdal.GetDriverByName('GTiff')
        # out_ds = driver.CreateCopy(out_raster, ds, strict=True)
        # out_ds = None

        return ''  # output_info['OUTPUT']

    def get_safe_file_name(self, raw_name: str, ext: str = None):
        name = raw_name.strip().replace(' ', '_').replace('__', '_')
        if ext is not None:
            name = name + ext
        return name


def parse_posix_path(path: str) -> str:
    """This method returns a posix path no matter if you pass it a windows or a linux path

    Args:
        path ([type]): [description]
    """
    new_path = PurePosixPath(path.replace('\\', '/'))
    return str(new_path)
