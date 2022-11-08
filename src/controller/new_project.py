import os
import sqlite3
from qgis.core import QgsField, QgsVectorLayer, QgsVectorFileWriter
from .qris_task import QRiSTask

layers = [
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
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point')
]


class NewProject(QRiSTask):

    def __init__(self, iface, db_path: str, project_name, description: str):
        """
        iface: QGIS interface
        db_path: Full absolute path to the QRiS GeoPackage
        project_name: QRiS project name
        description: QRiS project description
        """

        super().__init__(iface, 'New QRiS Project', 'NEW_QRIS_PROJECT')

        self.db_path = db_path
        self.project_name = project_name
        self.project_description = description

    def run(self):

        try:
            os.makedirs(os.path.dirname(self.db_path))
            # qris_project = QRiSProject(self.project_name)
            # qris_project.project_path = self.project_folder

            # Create the geopackage feature classes that will in turn cause the project geopackage to get created
            for fc_name, layer_name, geometry_type in layers:
                features_path = '{}|layername={}'.format(self.db_path, layer_name)
                create_geopackage_table(geometry_type, fc_name, self.db_path, features_path, None)

            # Run the schema DDL migrations to create lookup tables and relationships
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA foreign_keys = ON;')
            curs = conn.cursor()

            schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
            schema_file = open(schema_path, 'r')
            sql_commands = schema_file.read()
            curs.executescript(sql_commands)

            # Create the project
            curs.execute('INSERT INTO projects (name, description) VALUES (?, ?)', [self.project_name, self.project_description])
            conn.commit()
            conn.close()
            schema_file.close()

        except Exception as ex:
            self.exception = ex
            return False

        return True


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
    if os.path.exists(geopackage_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormat(memory_layer, geopackage_path, options)
