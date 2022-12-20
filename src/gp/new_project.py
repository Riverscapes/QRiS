import os
import sqlite3

from osgeo import ogr

from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsField, QgsVectorFileWriter
from qgis.PyQt.QtCore import pyqtSignal

MESSAGE_CATEGORY = 'QRiS_NewProjectTask'


class NewProjectTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    project_complete = pyqtSignal(bool)
    project_create_layers = pyqtSignal(int, int)
    project_create_schema = pyqtSignal()

    def __init__(self, project_name: str, output_gpkg: str, description: str, layers: dict):
        super().__init__('New QRIS Project Task', QgsTask.CanCancel)

        self.project_name = project_name
        self.project_description = description
        self.output_gpkg = output_gpkg
        self.layers = layers

    def run(self):
        """
        New QRIS project
        """

        self.setProgress(0)

        try:
            # Create the geopackage feature classes that will in turn cause the project geopackage to get created
            i = 1
            for fc_name, layer_name, geometry_type in self.layers:
                self.project_create_layers.emit(i, len(self.layers))
                features_path = '{}|layername={}'.format(self.output_gpkg, layer_name)
                self.create_geopackage_table(geometry_type, fc_name, self.output_gpkg, features_path, None)
                i += 1
            # self.setProgress(50)

            self.project_create_schema.emit()
            # Run the schema DDL migrations to create lookup tables and relationships
            conn = sqlite3.connect(self.output_gpkg)
            conn.execute('PRAGMA foreign_keys = ON;')
            curs = conn.cursor()

            schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
            schema_file = open(schema_path, 'r')
            sql_commands = schema_file.read()
            curs.executescript(sql_commands)

            # Create the project
            description = self.project_description if len(self.project_description) > 0 else None
            curs.execute('INSERT INTO projects (name, description) VALUES (?, ?)', [self.project_name, description])
            conn.commit()
            conn.close()
            schema_file.close()
            return True

        except Exception as ex:
            self.exception = ex
            return False

    def progress_callback(self, complete, message, unknown):
        self.setProgress(complete * 100)

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            QgsMessageLog.logMessage('Creation of new QRIS Project successful', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Creation of new QRIS Project not successful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Create New QRIS Project exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.project_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Create New QRIS Project was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    def create_geopackage_table(self, geometry_type: str, table_name: str, geopackage_path: str, full_path: str, field_tuple_list: list = None):
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
