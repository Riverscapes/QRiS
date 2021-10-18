import os
# from typing_extensions import ParamSpecKwargs

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant
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
        # self.txtLayerName.setText(layer_uri.name)
        # self.txtLayerSource.setText(layer_uri.uri)
        # self.cboLayerType.addItems(PROJECT_LAYER_TYPES)
        # self.text_validate()
        # self.txtLayerName.textChanged.connect(self.text_validate)
        # Checks whether the geopackage exists and creates it if not
        self.loadAssessmentDb()
        # add some button
        self.pushButton_save_assessment.clicked.connect(self.saveAssessment)
        self.pushButton_cancel_assessment.clicked.connect(self.cancel_assessment)

    # def text_validate(self):
    #     text = self.txtLayerName.text()
    #     out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
    #     self.txtProjectLayerPath.setText(os.path.join("ProjectLayers.gpkg", out_text))
    #     self.layer_path_name = out_text
    #     self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
    def loadAssessmentDb(self):
        """Checks if the assessments.gpkg exists, and creates it if it doesn't."""
        self.assessments_path = os.path.join(self.current_project.project_path, "assessments.gpkg")
        if not os.path.exists(self.assessments_path):
            # TODO this should not be a point layer, refactor to a table without geometry
            memory_assessments = QgsVectorLayer("NoGeometry", "assessments", "memory")
            # write to disk
            QgsVectorFileWriter.writeAsVectorFormat(memory_assessments, self.assessments_path, 'utf-8', driverName='GPKG', onlySelected=False)
            # access the layer
            self.assessments_layer = QgsVectorLayer(self.assessments_path + "|layername=assessments", "assessments", "ogr")
            # the data model
            assessment_date_field = QgsField("assessment_date", QVariant.Date)
            assessment_description_field = QgsField("assessment_description", QVariant.String)
            # add fields
            pr = self.assessments_layer.dataProvider()
            pr.addAttributes([assessment_date_field, assessment_description_field])
            self.assessments_layer.updateFields()

            # Add JAM layer
            # TODO flesh out attribute data model and rewrite as dataProvider
            jam_layer_uri = "point?crs=EPSG:4326&field=type:string&wood_count:string&index=yes"
            # create the layer in memory from the uri
            jam_layer_memory = QgsVectorLayer(jam_layer_uri, "jams", "memory")
            # setup the addition to the assessment geopackage
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = "jams"
            options.driverName = 'GPKG'
            if os.path.exists(self.assessments_path):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                QgsVectorFileWriter.writeAsVectorFormat(jam_layer_memory, self.assessments_path, options)

            # Add DAM layer
            # TODO flesh out attribute data model
            dam_layer_uri = "point?crs=EPSG:4326&field=type:string&dam_count:string&index=yes"
            # create the layer in memory from the uri
            dam_layer_memory = QgsVectorLayer(dam_layer_uri, "dams", "memory")
            # setup the addition to the assessment geopackage
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = "dams"
            options.driverName = 'GPKG'
            if os.path.exists(self.assessments_path):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                QgsVectorFileWriter.writeAsVectorFormat(dam_layer_memory, self.assessments_path, options)

            # TODO load other layers in the geopackage

    def saveAssessment(self):
        """Creates and saves a new assessment record to the db from the assessment dialog"""
        # set an index for the new deployment_id
        self.assessments_layer = QgsVectorLayer(self.assessments_path + "|layername=assessments", "assessments", "ogr")
        index_assessment_fid = self.assessments_layer.fields().indexOf("fid")
        # QMessageBox.information(None, "Runs when loaded", "stuff " + index_assessment_fid)
        new_assessment_fid = self.assessments_layer.maximumValue(index_assessment_fid) + 1
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

        # # TODO: Set the combo box based on the index of the site name
        # # set_to_index = self.comboBox_select_site.findText(new_site_name)
        # # self.comboBox_select_site.setCurrentIndex(set_to_index)
        # # close the dialog and clear the dialog object
        self.close()

        # out_name = self.txtLayerName.text()
        # out_gpkg = os.path.join(self.project.project_path, "ProjectLayers.gpkg")
        # original_layer = QgsVectorLayer(self.txtLayerSource.text())
        # if not os.path.exists(os.path.dirname(out_gpkg)):
        #     os.makedirs(os.path.dirname(os.path.dirname(out_gpkg)))
        # options = QgsVectorFileWriter.SaveVectorOptions()
        # options.layerName = self.layer_path_name
        # options.driverName = 'GPKG'
        # if os.path.exists(out_gpkg):
        #     options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # _out = QgsVectorFileWriter.writeAsVectorFormat(original_layer, out_gpkg, options)

        # self.project.project_layers[out_name] = Layer(out_name, self.txtProjectLayerPath.text(), self.cboLayerType.currentText())
        # self.project.export_project_file()

        # self.dataChange.emit(self.project, out_name)
        pass

    def cancel_assessment(self):
        self.close()
