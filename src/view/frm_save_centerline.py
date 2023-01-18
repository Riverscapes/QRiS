from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import QgsVectorLayer, QgsFeature

from ..model.project import Project
from ..model.profile import Profile, insert_profile

from .utilities import validate_name, add_standard_form_buttons


class FrmSaveCenterline(QtWidgets.QDialog):

    def __init__(self, parent, iface, project: Project):

        super(FrmSaveCenterline, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi()
        self.setWindowTitle('Create Centerline')

        # self.iface = iface
        self.project = project

        self.metrics = None
        self.fields = None
        self.geom_centerline = None

    def add_metrics(self, metrics: dict):
        """ metrics: dict(metric_name:value)
        """
        self.metrics = metrics
        row = self.tableMetrics.rowCount()
        for metric_name, value in self.metrics.items():
            self.tableMetrics.insertRow(row)
            self.tableMetrics.setItem(row, 0, QtWidgets.QTableWidgetItem(metric_name))
            self.tableMetrics.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value)))
            row += 1

    def add_fields(self, fields: dict):
        self.fields = fields

    def add_centerline(self, centerline):

        self.centerline_feat = centerline

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        try:
            profile = insert_profile(self.project.project_file, self.txtName, Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE, self.txtDescription)
            out_layer = QgsVectorLayer(f'{self.project.project_file}|layername=profile_centerlines')
            out_feature = QgsFeature()
            out_feature.setFields(out_layer.fields())
            out_feature[profile.id_column_name] = profile.id
            if self.fields is not None:
                for field, value in self.fields.items():
                    out_feature[field] = value
            # TODO save metrics somewhere
            out_layer.dataProvider().addFeature(out_feature)
            out_layer.commitChanges()

        except Exception as ex:
            try:
                profile.delete(self.project.project_file)
            except Exception as ex2:
                QtWidgets.QMessageBox.warning(self, 'Error attempting to delete centerline after the saving of features failed.', str(ex2))
            QtWidgets.QMessageBox.warning(self, 'Error Saving Centerline Feature', str(ex))
            return False

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
