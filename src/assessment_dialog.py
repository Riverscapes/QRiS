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

from .ript_project import RiptProject, Layer

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'assessment_dialog.ui'))

# PROJECT_LAYER_TYPES = ['Project_Extent']


class AssessmentDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(RiptProject, str)

    def __init__(self, current_project):
        """Constructor."""
        QDialog.__init__(self, None)
        self.setupUi(self)

        self.current_project = current_project
        self.assessments_path = os.path.join(self.current_project.project_path, "Assessments.gpkg")
        # create the db if it isn't there?
        if not os.path.exists(self.assessments_path):
            self.load_assessment_gpkg()
        # add signals to buttons
        self.pushButton_save_assessment.clicked.connect(self.save_assessment)
        self.pushButton_cancel_assessment.clicked.connect(self.cancel_assessment)

    # def text_validate(self):
    #     text = self.txtLayerName.text()
    #     out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
    #     self.txtProjectLayerPath.setText(os.path.join("ProjectLayers.gpkg", out_text))
    #     self.layer_path_name = out_text
    #     self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
    def load_assessment_gpkg(self):
        """Creates it if it doesn't."""
        # layer for creating the geopackage
        memory_create = QgsVectorLayer("NoGeometry", "memory_create", "memory")
        # write to disk
        QgsVectorFileWriter.writeAsVectorFormat(memory_create, self.assessments_path, 'utf-8', driverName='GPKG', onlySelected=False)

        # create assessments table and write to geopackage
        memory_assessments = QgsVectorLayer("NoGeometry", "memory_assessments", "memory")
        # copy the memory layer to the geopackage with a parent
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = "assessments"
        options.driverName = 'GPKG'
        if os.path.exists(self.assessments_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(memory_assessments, self.assessments_path, options)
            self.assessments_layer = QgsVectorLayer(self.assessments_path + "|layername=assessments", "assessments", "ogr")
            # the data model and add fields
            assessment_date_field = QgsField("assessment_date", QVariant.Date)
            assessment_description_field = QgsField("assessment_description", QVariant.String)
            pr = self.assessments_layer.dataProvider()
            pr.addAttributes([assessment_date_field, assessment_description_field])
            self.assessments_layer.updateFields()

        # add the dam table
        memory_dams = QgsVectorLayer("Point", "memory_dams", "memory")
        # copy the memory layer to the geopackage with a parent
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = "dams"
        options.driverName = 'GPKG'
        if os.path.exists(self.assessments_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(memory_dams, self.assessments_path, options)
            self.dams_layer = QgsVectorLayer(self.assessments_path + "|layername=dams", "dams", "ogr")
            # the data model and add fields to the layer
            assessment_id = QgsField("assessment_id", QVariant.Int)
            dam_type_field = QgsField("dam_type", QVariant.String)
            dam_description_field = QgsField("dam_description", QVariant.String)
            pr = self.dams_layer.dataProvider()
            pr.addAttributes([assessment_id, dam_type_field, dam_description_field])
            self.dams_layer.updateFields()

    def save_assessment(self):
        """Creates and saves a new assessment record to the db from the assessment dialog"""
        # set an index for the new deployment_idThird o
        # TODO get rid of this reference to assessments_layer here? It should be created above
        self.assessments_layer = QgsVectorLayer(self.assessments_path + "|layername=assessments", "assessments", "ogr")
        index_assessment_fid = self.assessments_layer.fields().indexOf("fid")
        # use try because does not like a max value of 0
        try:
            new_assessment_fid = self.assessments_layer.maximumValue(index_assessment_fid) + 1
        except TypeError:
            new_assessment_fid = 1
        # # grab the form values
        new_assessment_date = self.dateEdit_assessment_date.date()
        new_assessment_description = self.plainTextEdit_assessment_description.toPlainText()
        # # create a blank QgsFeature that copies the deployemnt table
        new_assessment_feature = QgsFeature(self.assessments_layer.fields())
        # # set the form values to the feature
        new_assessment_feature.setAttribute("fid", new_assessment_fid)
        new_assessment_feature.setAttribute("assessment_date", new_assessment_date)
        new_assessment_feature.setAttribute("assessment_description", new_assessment_description)
        # # TODO add ability to manually enter lat long?
        pr = self.assessments_layer.dataProvider()
        pr.addFeatures([new_assessment_feature])

        # get an assessment name
        new_assessment_name = new_assessment_date.toString('yyyy-MM-dd')
        # create a ript_project.Layer constructor
        # TODO double check what the path looks like for other layers?
        self.current_project.project_assessments = True
        # TODO call export file to write that shit to the xml
        self.current_project.export_project_file()
        # TODO pass in the name of the new node here for the add to map function
        self.dataChange.emit(self.current_project, "Riverscape Assessments")
        self.close()

    def cancel_assessment(self):
        self.close()
