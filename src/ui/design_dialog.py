import os
# from typing_extensions import ParamSpecKwargs

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QDate
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
        self.structure_zoi_path = self.geopackage_path + '|layername=structure_zoi'
        self.structures_field_path = self.geopackage_path + '|layername=structures_field'
        self.structures_desktop_path = self.geopackage_path + '|layername=structures_desktop'

        # population combo boxes
        list_of_design_sources = ['desktop', 'field']
        list_of_design_types = ['as-built', 'design']
        self.comboBox_design_source.addItems(list_of_design_sources)
        self.comboBox_design_type.addItems(list_of_design_types)

        # add signals to buttons
        self.buttonBox.accepted.connect(self.save_design)
        self.buttonBox.rejected.connect(self.cancel_design)

        # create the db if it isn't there?
        if not os.path.exists(self.geopackage_path):
            self.create_design_geopackage()

    def create_design_geopackage(self):
        """Creates design directory, geopackage, and tables"""
        # check if the directory exists
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

        # # Create the geopackage and design table
        # memory_designs = QgsVectorLayer("NoGeometry", "memory_designs", "memory")
        # design_name = QgsField("design_name", QVariant.String)
        # design_source = QgsField("design_source", QVariant.String)
        # design_type = QgsField("design_type", QVariant.String)
        # design_description = QgsField("design_description", QVariant.String)
        # pr = memory_designs.dataProvider()
        # pr.addAttributes([design_name, design_source, design_type, design_description])
        # memory_designs.updateFields()

        # options = QgsVectorFileWriter.SaveVectorOptions()
        # options.layerName = "designs"
        # options.driverName = 'GPKG'
        # if os.path.exists(self.geopackage_path):
        #     options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        # QgsVectorFileWriter.writeAsVectorFormat(memory_designs, self.geopackage_path, options)

        create_geopackage_table('NoGeometry', 'designs', self.geopackage_path, self.designs_path,
                                [
                                    ('design_name', QVariant.String),
                                    ('design_source', QVariant.String),
                                    ('design_type', QVariant.String),
                                    ('design_description', QVariant.String),
                                ])

        create_geopackage_table('NoGeometry', 'structure_types', self.geopackage_path, self.structure_types_path,
                                [
                                    ('structure_type_name', QVariant.String),
                                    ('structure_mimics', QVariant.String),
                                    ('construction_description', QVariant.String),
                                    ('function_description', QVariant.String),
                                    ('average_length', QVariant.Double),
                                    ('average_width', QVariant.Double),
                                    ('average_height', QVariant.Double),
                                    ('post_spacing', QVariant.Double)
                                ])

        create_geopackage_table('Polygon', 'structure_zoi', self.geopackage_path, self.structure_zoi_path,
                                [
                                    ('design_id', QVariant.Int),
                                    ('zoi_name', QVariant.String),
                                    ('zoi_type', QVariant.String),
                                    ('zoi_description', QVariant.String),
                                ])

        create_geopackage_table('Point', 'structures_field', self.geopackage_path, self.structures_field_path,
                                [
                                    ('design_id', QVariant.Int),
                                    ('structure_type_id', QVariant.Int),
                                    ('structure_description', QVariant.String),
                                ])

        create_geopackage_table('Linestring', 'structures_desktop', self.geopackage_path, self.structures_desktop_path,
                                [
                                    ('design_id', QVariant.Int),
                                    ('structure_type_id', QVariant.Int),
                                    ('structure_description', QVariant.String),
                                ])

    def save_design(self):
        """Creates and saves a new design record to the db from the design dialog"""
        self.designs_layer = QgsVectorLayer(self.designs_path, "designs", "ogr")
        index_design_fid = self.designs_layer.fields().indexOf("fid")
        # use try because does not like a max value of 0
        if self.designs_layer.featureCount() > 0:
            new_design_fid = self.designs_layer.maximumValue(index_design_fid) + 1
        else:
            new_design_fid = 1
        # # grab the form values
        new_design_name = self.lineEdit_design_name.text()
        new_design_source = self.comboBox_design_source.currentText()
        new_design_type = self.comboBox_design_type.currentText()
        new_design_description = self.plainTextEdit_design_description.toPlainText()
        # create a blank QgsFeature that copies the deployemnt table
        new_design_feature = QgsFeature(self.designs_layer.fields())
        # # set the form values to the feature
        new_design_feature.setAttribute("fid", new_design_fid)
        new_design_feature.setAttribute("design_name", new_design_name)
        new_design_feature.setAttribute("design_source", new_design_source)
        new_design_feature.setAttribute("design_type", new_design_type)
        new_design_feature.setAttribute("design_description", new_design_description)
        pr = self.designs_layer.dataProvider()
        pr.addFeatures([new_design_feature])
        self.dataChange.emit(self.qris_project, new_design_name)
        self.close()

    def cancel_design(self):
        self.close()
