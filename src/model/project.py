import os
import sqlite3

from .basis import Basis

from .assessment import Assessment
from .db_item import DBItem

from pathlib import Path, PurePosixPath

from qgis import processing


class Project():

    def __init__(self, project_file: str):

        self.project_file = project_file
        conn = sqlite3.connect(project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()

        curs.execute('SELECT name FROM projects LIMIT 1')
        self.name = curs.fetchone()['name']

        curs.execute('SELECT fid, name FROM assessments')
        self.assessments = {row['name']: row['fid'] for row in curs.fetchall()}

    def add_assessment(self, name: str, description: str, methods: list, bases: list) -> Assessment:

        conn = sqlite3.connect(self.project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute('INSERT INTO assessments (name, description) VALUES (?, ?)', [name, description if len(description) > 1 else None])
        assessment_id = curs.lastrowid

        assessment_methods = [(assessment_id, method_id) for method_id in methods]
        curs.executemany("""INSERT INTO assessment_methods (assessment_id, method_id)
                    SELECT ?, fid FROM methods WHERE name = ?""", assessment_methods)
        conn.commit()

        # Hack because listview only stores the method strings
        curs.execute('SELECT am.fid, m.name FROM assessment_methods am INNER JOIN methods m ON am.method_id = m.fid WHERE assessment_id = ?', [assessment_id])
        methods = {row['fid']: row['name'] for row in curs.fetchall()}

        assessment_bases = [(assessment_id, base_name) for base_name in bases]
        curs.executemany("""INSERT INTO assessment_bases (assessment_id, base_id)
                    SELECT ?, fid FROM bases WHERE name = ?""", assessment_bases)
        conn.commit()

        # Hack because listview only stores the strings
        # curs.execute('SELECT am.fid, m.name FROM assessment_bases am INNER JOIN bases m ON am.base_id = m.fid WHERE assessment_id = ?', [assessment_id])
        bases = {}  # {row['fid']: row['name'] for row in curs.fetchall()}

        return Assessment(assessment_id, name, description, methods, bases)

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


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
