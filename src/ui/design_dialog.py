import os
import sqlite3

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QDateTime
from qgis.core import (
    Qgis,
    QgsProject,
    QgsField,
    QgsFeature,
    QgsVectorLayer,
    QgsVectorFileWriter
)

from ..qris_project import QRiSProject

from ..QRiS.functions import create_geopackage_table

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'design_dialog.ui'))


class DesignDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, qris_project):
        """Used to construct the design dialog"""
        QDialog.__init__(self, None)
        self.setupUi(self)
        self.qris_project = qris_project
        # paths to directory geopackage and tables
        self.directory_path = self.qris_project.project_designs.directory_path(self.qris_project.project_path)
        self.geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        self.designs_path = self.geopackage_path + '|layername=designs'
        self.structure_types_path = self.geopackage_path + '|layername=structure_types'
        self.status_path = self.geopackage_path + '|layername=design_status'
        self.phases_path = self.geopackage_path + '|layername=phases'
        self.zoi_path = self.geopackage_path + '|layername=zoi'
        self.complexes_path = self.geopackage_path + '|layername=complexes'
        self.structure_points_path = self.geopackage_path + '|layername=structure_points'
        self.structure_lines_path = self.geopackage_path + '|layername=structure_lines'

        # create the db if it isn't there?
        if not os.path.exists(self.geopackage_path):
            self.create_design_geopackage()

        # populate combo boxes
        conn = sqlite3.connect(self.geopackage_path)
        curs = conn.cursor()
        curs.execute('SELECT * FROM design_status')
        statuses = curs.fetchall()
        conn.close()
        for status in statuses:
            self.comboBox_design_status.addItem(status[1], status[0])
        self.comboBox_design_geometry.addItems(['Point', 'Line'])

        # add signals to buttons
        self.buttonBox.accepted.connect(self.save_design)
        self.buttonBox.rejected.connect(self.cancel_design)

    def create_design_geopackage(self):
        """Creates design directory, geopackage, and tables"""
        # check if the directory exists
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

        # # Create the geopackage and design table
        # memory_designs = QgsVectorLayer("NoGeometry", "memory_designs", "memory")
        # design_name = QgsField("design_name", QVariant.String)
        # design_geometry = QgsField("design_geometry", QVariant.String)
        # design_status = QgsField("design_status", QVariant.String)
        # design_description = QgsField("design_description", QVariant.String)
        # pr = memory_designs.dataProvider()
        # pr.addAttributes([design_name, design_geometry, design_status, design_description])
        # memory_designs.updateFields()

        # options = QgsVectorFileWriter.SaveVectorOptions()
        # options.layerName = "designs"
        # options.driverName = 'GPKG'
        # if os.path.exists(self.geopackage_path):
        #     options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        # QgsVectorFileWriter.writeAsVectorFormat(memory_designs, self.geopackage_path, options)

        create_geopackage_table('Polygon', 'zoi', self.geopackage_path, self.zoi_path,
                                [
                                    ('influence', QVariant.String),
                                    ('description', QVariant.String),
                                ])
        create_geopackage_table('Polygon', 'complexes', self.geopackage_path, self.complexes_path,
                                [
                                    # ('design_id', QVariant.Int),
                                    ('name', QVariant.String),
                                    ('description', QVariant.String),
                                    ('initial_condition', QVariant.String),
                                    ('target_condition', QVariant.String),
                                ])

        create_geopackage_table('Point', 'structure_points', self.geopackage_path, self.structure_points_path,
                                [
                                    # ('design_id', QVariant.Int),
                                    # ('structure_type_id', QVariant.Int),
                                    # ('phase_id', QVariant.Int),
                                    ('name', QVariant.String),
                                    ('description', QVariant.String),
                                ])

        create_geopackage_table('Linestring', 'structure_lines', self.geopackage_path, self.structure_lines_path,
                                [
                                    # ('design_id', QVariant.Int),
                                    # ('structure_type_id', QVariant.Int),
                                    # ('phase_id', QVariant.Int),
                                    ('name', QVariant.String),
                                    ('description', QVariant.String),
                                ])

        # SQL for non spatial tables, initial values, and data relationships
        conn = sqlite3.connect(self.geopackage_path)
        conn.execute('PRAGMA foreign_keys = ON;')
        curs = conn.cursor()
        sql_path = os.path.dirname(os.path.dirname(__file__))
        design_schema_path = os.path.join(sql_path, "sql", "design_schema.sql")
        design_qry_string = open(design_schema_path, 'r').read()
        curs.executescript(design_qry_string)
        conn.commit()
        conn.close()

    # These initial values are now implemented in SQL
    # def populate_standard_phases(self):
    #     """Populates the phase table with a starting set of phases"""
    #     standard_phases = ['Pilot', 'Phase 1', 'Phase 2']
    #     self.phases = QgsVectorLayer(self.phases_path, "phases", "ogr")

    #     standard_fid = 1
    #     for standard_name in standard_phases:
    #         new_phase_feature = QgsFeature(self.phases.fields())
    #         new_phase_feature.setAttribute("fid", standard_fid)
    #         new_phase_feature.setAttribute("phase_name", standard_name)
    #         new_phase_feature.setAttribute("dominate_action", "New Structure Additions")
    #         self.phases.dataProvider().addFeatures([new_phase_feature])
        # standard_fid += 1

    # def populate_standard_structure_types(self):
    #     """Populates the structure types table with a starting set of structure types and attributes"""
    #     # TODO turn these into a dictionary with all values for each type
    #     standard_bda = ['BDA Large', 'BDA Small', 'BDA Postless']
    #     standard_pals = ['PALS Bank Attached', 'PALS Mid-Channel', 'Wood Jam']
    #     self.structure_types_layer = QgsVectorLayer(self.structure_types_path, "structure_types", "ogr")

    #     standard_fid = 1
    #     for standard_name in standard_bda:
    #         new_structure_feature = QgsFeature(self.structure_types_layer.fields())
    #         new_structure_feature.setAttribute("fid", standard_fid)
    #         new_structure_feature.setAttribute("structure_type_name", standard_name)
    #         new_structure_feature.setAttribute("structure_mimics", "Beaver Dam")
    #         self.structure_types_layer.dataProvider().addFeatures([new_structure_feature])
    #         standard_fid += 1

    #     for standard_name in standard_pals:
    #         new_structure_feature = QgsFeature(self.structure_types_layer.fields())
    #         new_structure_feature.setAttribute("fid", standard_fid)
    #         new_structure_feature.setAttribute("structure_type_name", standard_name)
    #         new_structure_feature.setAttribute("structure_mimics", "Woody Debris")
    #         self.structure_types_layer.dataProvider().addFeatures([new_structure_feature])
    #         standard_fid += 1

    # TODO Refactor to be an sql insert statement
    def save_design(self):
        """Creates and saves a new design record to the db from the design dialog"""
        self.designs_layer = QgsVectorLayer(self.designs_path, "designs", "ogr")
        index_design_fid = self.designs_layer.fields().indexOf("fid")
        if self.designs_layer.featureCount() > 0:
            new_design_fid = self.designs_layer.maximumValue(index_design_fid) + 1
        else:
            new_design_fid = 1
        # # grab the form values
        new_design_name = self.lineEdit_design_name.text()
        new_design_geometry = self.comboBox_design_geometry.currentText()
        new_design_status = self.comboBox_design_status.currentData()
        new_design_description = self.plainTextEdit_design_description.toPlainText()
        # create a blank QgsFeature that copies the deployemnt table
        new_design_feature = QgsFeature(self.designs_layer.fields())
        # # set the form values to the feature
        new_design_feature.setAttribute("fid", new_design_fid)
        new_design_feature.setAttribute("name", new_design_name)
        new_design_feature.setAttribute("structure_geometry", new_design_geometry)
        new_design_feature.setAttribute("status_id", new_design_status)
        new_design_feature.setAttribute("description", new_design_description)
        new_design_feature.setAttribute("created", QDateTime.currentDateTime())
        pr = self.designs_layer.dataProvider()
        pr.addFeatures([new_design_feature])
        self.dataChange.emit(self.qris_project, new_design_name)
        self.close()

    def cancel_design(self):
        self.close()
