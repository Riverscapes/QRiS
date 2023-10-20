import os
import json
import shutil

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QDateTime

from qgis import processing
from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgRunnerTask, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer, QgsVectorLayerUtils

from ..model.event_layer import EventLayer
from ..model.project import Project

from .utilities import add_standard_form_buttons


class FrmImportPhotos(QtWidgets.QDialog):
    def __init__(self, parent, qris_project: Project, event_layer: EventLayer, photo_folder: str):
        super().__init__(parent=parent)

        self.qris_project = qris_project
        self.event_layer = event_layer

        self.setWindowTitle("Import Photos")
        self.setModal(True)
        self.setupUi()

        self.txt_folder.setText(photo_folder)
        self.show_preview()

    def browse_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.txt_folder.setText(folder_path)
            self.show_preview()

    def show_preview(self):
        folder_path = self.txt_folder.text()

        if folder_path is None or folder_path == "":
            return
        if not os.path.isdir(folder_path):
            return

        # Show first photo in folder as preview
        files = os.listdir(folder_path)
        for file in files:
            if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                file_path = os.path.join(folder_path, file)
                pixmap = QPixmap(file_path)
                self.lbl_preview.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
                break

    def accept(self) -> None:
        folder_path = self.txt_folder.text()

        if folder_path is None or folder_path == "":
            QtWidgets.QMessageBox.critical(self, "Error", "Please select a folder.")
            return

        if not os.path.isdir(folder_path):
            return

        # Create dce photo folder
        dce_photo_folder = os.path.join(os.path.dirname(self.qris_project.project_file), "photos", f'dce_{str(self.event_layer.event_id).zfill(3)}')
        if not os.path.isdir(dce_photo_folder):
            os.makedirs(dce_photo_folder)

        # get a list of existing photos in the dce_photo_folder (could be 0)
        self.existing_photos = []
        for file in os.listdir(dce_photo_folder):
            if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                self.existing_photos.append(file)

        # Copy photos to dce photo folder using naming convention YYYY_MM_DD_photo_number (e.g. 2021_01_01_0001)
        files = os.listdir(folder_path)
        photo_number = 1
        for file in files:
            if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                file_path = os.path.join(folder_path, file)
                # just use the existing file name for now
                file_name = os.path.basename(file_path)
                new_file_path = os.path.join(dce_photo_folder, file_name)
                shutil.copy(file_path, new_file_path)
                photo_number += 1

        # use the processing algorithm to create the photo layer
        context = QgsProcessingContext()
        params = {
            'FOLDER': dce_photo_folder,
            'RECURSIVE': False,
            # 'OUTPUT': """ogr:dbname=\'D:/NAR_Data/QRIS/photo_experiment/photos.gpkg\' table="Photos" (geom)"""
            'OUTPUT': 'memory:Photos'
        }

        result = processing.run("native:importphotos", params)
        self.task_finished(context, True, result)

        # return super().accept()

    def task_finished(self, context: QgsProcessingContext, successful, results):
        if not successful:
            QgsMessageLog.logMessage('Task finished unsucessfully',
                                     "Import Photos Qgis Processing",
                                     Qgis.Warning)
        output_layer = results['OUTPUT']

        if output_layer.isValid():
            working_layer: QgsVectorLayer = output_layer  # context.takeResultLayer(output_layer.id())

            # we need to copy the features from the working layer to the event layer
            # we need to set the event_id field to the event_id of the event layer
            # we need to add the attributes as a metadata json field
            out_layer = QgsVectorLayer(f"{self.qris_project.project_file}|layername=dce_points", "dce_points", "ogr")
            new_features = []
            for feature in working_layer.getFeatures():
                # check if the photo already exists in the event layer
                if os.path.basename(feature['photo']) in self.existing_photos:
                    continue
                # take all the attributes from the working layer and turn them into a json string
                metadata = {}
                for field in working_layer.fields():
                    data = feature[field.name()]
                    if data is not None:
                        name = field.name()
                        if isinstance(data, QDateTime):
                            data = data.toString(Qt.ISODate)
                        if name == 'photo':
                            metadata['Photo Path'] = os.path.basename(data)
                            # data = data.replace('\\', '/')
                            # name = "Photo Path"
                    metadata[name] = data
                metadata['Observation Type'] = "Photo Observation"
                metadata_json = json.dumps(metadata)
                # create a new feature in the event layer
                new_feature = QgsVectorLayerUtils.createFeature(out_layer)
                new_feature.setGeometry(feature.geometry())
                new_feature.setAttribute('event_id', self.event_layer.event_id)
                new_feature.setAttribute('event_layer_id', self.event_layer.layer.id)
                new_feature.setAttribute('metadata', metadata_json)
                new_features.append(new_feature)
            out_layer.dataProvider().addFeatures(new_features)
            out_layer.updateExtents()

        return super().accept()

    def setupUi(self):

        # Create layout
        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)
        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        # Create widgets
        self.lbl_folder = QtWidgets.QLabel("Folder Path")
        self.grid.addWidget(self.lbl_folder, 0, 0)

        horiz_folder = QtWidgets.QHBoxLayout()
        self.grid.addLayout(horiz_folder, 0, 1)

        self.txt_folder = QtWidgets.QLineEdit()
        self.txt_folder.setReadOnly(True)
        horiz_folder.addWidget(self.txt_folder)

        self.btn_browse = QtWidgets.QPushButton("...")
        self.btn_browse.clicked.connect(self.browse_folder)
        horiz_folder.addWidget(self.btn_browse)

        self.lbl_preview = QtWidgets.QLabel()
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.grid.addWidget(self.lbl_preview, 1, 1, 1, 2)

        self.vert.addLayout(add_standard_form_buttons(self, 'photos'))
