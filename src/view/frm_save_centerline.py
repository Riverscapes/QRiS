import json

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry

from ..model.project import Project
from ..model.profile import Profile, insert_profile

from .metadata import MetadataWidget

from .utilities import validate_name, add_standard_form_buttons


class FrmSaveCenterline(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, centerline_geom: QgsGeometry, metrics: dict = None, system_metadata: dict = None):

        super(FrmSaveCenterline, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # metadata_json = json.dumps(system_metadata) if system_metadata is not None else None
        self.metadata_widget = MetadataWidget(self, None)
        for key, value in system_metadata.items():
            self.metadata_widget.add_system_metadata(key, value)

        self.setupUi()
        self.setWindowTitle('Create Centerline')

        self.project = project
        self.metrics = metrics
        self.centerline_geom = centerline_geom
        self.profile = None

        self.add_metrics()

    def add_metrics(self, metrics: dict = None):
        """ metrics: dict(metric_name:value)
        """
        if metrics is not None:
            self.metrics = metrics
        row = self.tableMetrics.rowCount()
        for metric_name, value in self.metrics.items():
            self.tableMetrics.insertRow(row)
            self.tableMetrics.setItem(row, 0, QtWidgets.QTableWidgetItem(metric_name))
            self.tableMetrics.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value)))
            row += 1

    def accept(self):

        if not validate_name(self, self.txtName):
            return
        try:
            
            for key, value in self.metrics.items():
                self.metadata_widget.add_attribute_metadata(key, value)

            metadata_json = self.metadata_widget.get_json()
            out_metadata = json.loads(metadata_json) if metadata_json is not None else None

            self.profile = insert_profile(self.project.project_file, self.txtName.text(), Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE, self.txtDescription.toPlainText(), out_metadata)
            out_layer = QgsVectorLayer(f'{self.project.project_file}|layername=profile_centerlines')
            out_feature = QgsFeature()
            out_feature.setFields(out_layer.fields())
            out_feature.setGeometry(self.centerline_geom)
            out_feature['profile_id'] = self.profile.id
            if out_metadata is not None:
                out_feature.setAttribute('metadata', json.dumps(out_metadata))
            out_layer.dataProvider().addFeature(out_feature)
            out_layer.commitChanges()

        except Exception as ex:
            try:
                if self.profile is not None:
                    self.profile.delete(self.project.project_file)
            except Exception as ex2:
                QtWidgets.QMessageBox.warning(self, 'Error attempting to delete centerline after the saving of features failed.', str(ex2))
            QtWidgets.QMessageBox.warning(self, 'Error Saving Centerline Feature', str(ex))
            super(FrmSaveCenterline, self).reject()

        super(FrmSaveCenterline, self).accept()

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.tabs = QtWidgets.QTabWidget()
        self.tabDesc = QtWidgets.QWidget()
        self.tabMetrics = QtWidgets.QWidget()

        self.tabs.addTab(self.tabDesc, 'Description')
        self.tabs.addTab(self.tabMetrics, 'Metrics')
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.tabDesc.layout = QtWidgets.QVBoxLayout()
        self.tabDesc.setLayout(self.tabDesc.layout)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tabDesc.layout.addWidget(self.txtDescription)

        self.tabMetrics.layout = QtWidgets.QVBoxLayout()
        self.tabMetrics.setLayout(self.tabMetrics.layout)

        self.tableMetrics = QtWidgets.QTableWidget()
        self.tableMetrics.setColumnCount(2)
        self.tableMetrics.horizontalHeader().hide()
        self.tableMetrics.verticalHeader().hide()
        self.tabMetrics.layout.addWidget(self.tableMetrics)

        # self.tabMetrics.layout.addStretch()

        self.vert.addWidget(self.tabs)

        # self.chkAddToMap = QtWidgets.QCheckBox()
        # self.chkAddToMap.setText('Add to Map')
        # self.chkAddToMap.setChecked(True)
        # self.grid.addWidget(self.chkAddToMap, 6, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'centerlines'))
