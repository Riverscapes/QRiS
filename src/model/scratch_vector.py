import os
import sqlite3
import json

from .db_item import DBItem
from osgeo import ogr

from qgis.core import QgsMessageLog, Qgis
from ..QRiS.path_utilities import parse_posix_path

SCRATCH_VECTOR_MACHINE_CODE = 'Scratch Vectors'
CONTEXT_PARENT_FOLDER = 'context'


class ScratchVector(DBItem):

    def __init__(self, id: int, name: str, fc_name: str, gpkg_path: str, vector_type_id: int, description: str, metadata: dict = None):
        super().__init__('scratch_vectors', id, name)

        self.fc_name = fc_name
        self.gpkg_path = gpkg_path
        self.vector_type_id = vector_type_id
        self.description = description
        self.metadata = metadata
        self.icon = 'vector'

    def update(self, db_path: str, name: str, description: str, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE scratch_vectors SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex

    def delete(self, db_path: str) -> None:

        gpkg_path = scratch_gpkg_path(db_path)
        driver = ogr.GetDriverByName('GPKG')
        if os.path.exists(gpkg_path):
            data_source = driver.Open(gpkg_path, 1)

            for i in range(data_source.GetLayerCount()):
                layer = data_source.GetLayerByIndex(i)
                if layer.GetName() == self.fc_name:
                    data_source.DeleteLayer(i)
                    break
            data_source = None

            # Count the number of scratch layers
            # Remove the Scratch Geopackage and folder if empty
            try:
                layer_count = 1
                with sqlite3.connect(gpkg_path) as conn:
                    curs = conn.cursor()
                    curs.execute('SELECT count(*) from gpkg_contents')
                    layer_count = curs.fetchone()[0]

                # Connection must be closed to delete
                if layer_count < 1:
                    os.remove(gpkg_path)

                # Remove scratch folder if empty
                if len(os.listdir(os.path.dirname(gpkg_path))) == 0:
                    os.remove(os.path.dirname(gpkg_path))

            except Exception as ex:
                # Do nothing. This is nice to have
                QgsMessageLog.logMessage(f'Error Cleaning Vector Scratch Space: {ex}', 'QRiS', Qgis.Critical)

        # absolute_path = os.path.join(os.path.dirname(db_path), self.path)

        # if os.path.isfile(gpkg_path):
        #     raster = QgsVectorLayer(absolute_path)
        #     raster.dataProvider().remove()

        super().delete(db_path)


def load_scratch_vectors(curs: sqlite3.Cursor, project_file: str) -> dict:
    """ Scratch vectors are referenced in the QRiS project but also
    must have a corresponding feature class in the scratch geopackage (if it exists)"""

    geopackage_path = scratch_gpkg_path(project_file)
    if not os.path.exists(geopackage_path):
        return {}

    # Get a list of all feature classes in the GeoPackage.
    with sqlite3.connect(geopackage_path) as gpkg_conn:
        gpkg_curs = gpkg_conn.cursor()
        gpkg_curs.execute("SELECT table_name FROM gpkg_contents WHERE data_type = 'features'")
        feature_classes = {row[0]: None for row in gpkg_curs.fetchall()}

    # Only load scratch vectors that have a feature class
    scratch_vectors = {}
    curs.execute('SELECT * FROM scratch_vectors')
    for row in curs.fetchall():
        if row['fc_name'] in feature_classes:
            scratch_vectors[row['id']] = ScratchVector(
                row['id'],
                row['name'],
                row['fc_name'],
                geopackage_path,
                row['vector_type_id'],
                row['description'],
                json.loads(row['metadata']) if row['metadata'] is not None else None
            )

    return scratch_vectors


def insert_scratch_vector(db_path: str, name: str, fc_name: str, gpkg_path: str, vector_type_id: int, description: str, metadata: dict = None) -> ScratchVector:

    result = None
    metadata_json = json.dumps(metadata) if metadata is not None else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO scratch_vectors (name, fc_name, vector_type_id, description, metadata) VALUES (?, ?, ?, ?, ?)', [name, fc_name, vector_type_id, description, metadata_json])
            id = curs.lastrowid
            result = ScratchVector(id, name, fc_name, gpkg_path, vector_type_id, description, metadata)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result


def scratch_gpkg_path(project_file: str) -> str:

    return parse_posix_path(os.path.join(os.path.dirname(project_file), CONTEXT_PARENT_FOLDER, 'feature_classes.gpkg'))


def get_unique_scratch_fc_name(project_file: str, fc_seed_name: str):

    # If the scratch geopackage doesn't exist then the name must be unique
    gpkg_path = scratch_gpkg_path(project_file)
    if not os.path.isfile(gpkg_path):
        return fc_seed_name

    with sqlite3.connect(gpkg_path) as conn:
        curs = conn.cursor()
        fc_name = fc_seed_name
        attempts = 0
        name_exists = True
        while name_exists is True:
            if attempts > 0:
                fc_name = fc_seed_name + str(attempts)

            curs.execute('SELECT count(*) FROM gpkg_contents WHERE table_name = ?', [fc_name])
            rows = curs.fetchone()[0]
            if rows < 1:
                name_exists = False

            attempts += 1

    return fc_name
