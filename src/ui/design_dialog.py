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
        self.qris_project.designs_path = os.path.join(self.qris_project.project_path, "Designs.gpkg")
        # create the db if it isn't there?
        if not os.path.exists(self.qris_project.designs_path):
            self.load_design_gpkg()
        # add signals to buttons
        self.lineEdit_design_name.textChanged.connect(self.text_validate)
        self.pushButton_save_design.clicked.connect(self.save_design)
        self.pushButton_cancel_design.clicked.connect(self.cancel_design)

    # TODO add a function for formating design names
    def text_validate(self):
        text = self.lineEdit_design_name.text()
        formatted_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
        self.label_formatted_name.setText(formatted_text)
        self.clean_name = formatted_text
        return self.clean_name

    def load_design_gpkg(self):
        """Creates it if it ain't."""
        # layer for creating the geopackage
        memory_create = QgsVectorLayer("NoGeometry", "memory_create", "memory")
        # write to disk
        QgsVectorFileWriter.writeAsVectorFormat(memory_create, self.qris_project.designs_path, 'utf-8', driverName='GPKG', onlySelected=False)

        # create designs table and write to geopackage
        memory_designs = QgsVectorLayer("NoGeometry", "memory_designs", "memory")
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = "designs"
        options.driverName = 'GPKG'
        if os.path.exists(self.qris_project.designs_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(memory_designs, self.qris_project.designs_path, options)
            self.designs_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=designs", "designs", "ogr")
            design_name_field = QgsField("design_name", QVariant.String)
            design_description_field = QgsField("design_description", QVariant.String)
            pr = self.designs_layer.dataProvider()
            pr.addAttributes([design_name_field, design_description_field])
            self.designs_layer.updateFields()

        # add complexes layer
        memory_complexes = QgsVectorLayer("Polygon", "memory_complexs", "memory")
        # copy the memory layer to the geopackage with a parent
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = "complexes"
        options.driverName = 'GPKG'
        if os.path.exists(self.qris_project.designs_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(memory_complexes, self.qris_project.designs_path, options)
            self.complexes_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=complexes", "complexes", "ogr")
            design_id = QgsField("design_id", QVariant.Int)
            complex_description_field = QgsField("complex_description", QVariant.String)
            pr = self.complexes_layer.dataProvider()
            pr.addAttributes([design_id, complex_description_field])
            self.complexes_layer.updateFields()

        # add structures layer
        memory_structures = QgsVectorLayer("LineString", "memory_structures", "memory")
        # copy the memory layer to the geopackage with a parent
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = "structures"
        options.driverName = 'GPKG'
        if os.path.exists(self.qris_project.designs_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(memory_structures, self.qris_project.designs_path, options)
            self.structures_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=structures", "structures", "ogr")
            # the data model and add fields to the layer
            design_id = QgsField("design_id", QVariant.Int)
            structure_type_field = QgsField("structure_type", QVariant.String)
            structure_description_field = QgsField("structure_description", QVariant.String)
            structure_phase_field = QgsField("structure_phase", QVariant.String)
            pr = self.structures_layer.dataProvider()
            pr.addAttributes([design_id, structure_type_field, structure_description_field, structure_phase_field])
            self.structures_layer.updateFields()

    def save_design(self):
        """Creates and saves a new design record to the db from the design dialog"""
        self.designs_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=designs", "designs", "ogr")
        index_design_fid = self.designs_layer.fields().indexOf("fid")
        # use try because does not like a max value of 0
        try:
            new_design_fid = self.designs_layer.maximumValue(index_design_fid) + 1
        except TypeError:
            new_design_fid = 1
        # # grab the form values
        new_design_name = self.clean_name
        new_design_description = self.plainTextEdit_design_description.toPlainText()
        # create a blank QgsFeature that copies the deployemnt table
        new_design_feature = QgsFeature(self.designs_layer.fields())
        # # set the form values to the feature
        new_design_feature.setAttribute("fid", new_design_fid)
        new_design_feature.setAttribute("design_name", new_design_name)
        new_design_feature.setAttribute("design_description", new_design_description)
        # # TODO add ability to manually enter lat long?
        pr = self.designs_layer.dataProvider()
        pr.addFeatures([new_design_feature])
        # tell the project that there are now designs
        self.qris_project.project_designs = True
        # TODO call export file to write that shit to the xml
        self.qris_project.export_project_file()
        # TODO pass in the name of the new node here for the add to map function
        self.dataChange.emit(self.qris_project, new_design_name)
        self.close()

    def cancel_design(self):
        self.close()
