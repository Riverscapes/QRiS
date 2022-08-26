import os

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis import core, gui, utils

from ..model.analysis import Analysis, insert_analysis
from ..model.basemap import BASEMAP_PARENT_FOLDER, Raster, insert_raster
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import REGULAR_MASK_TYPE_ID


class FrmAnalysisProperties(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, analysis: Analysis = None):

        self.project = project
        self.analysis = analysis

        super(FrmAnalysisProperties, self).__init__(parent)
        self.setupUi()

        # Masks (filtered to just regular masks )
        self.masks = {id: mask for id, mask in project.masks.items() if mask.mask_type.id == REGULAR_MASK_TYPE_ID}
        self.masks_model = DBItemModel(self.masks)
        self.cboMask.setModel(self.masks_model)

        # Basemaps
        self.basemaps_model = DBItemModel(project.basemaps())
        self.cboBasemap.setModel(self.basemaps_model)

        self.metrics_model = QtGui.QStandardItemModel(len(project.metrics), 2)
        metrics = list(project.metrics.values())
        for row in range(len(metrics) - 1):
            metric = metrics[row]
            item = QtGui.QStandardItem(metric.name)
            item.setData(metric, QtCore.Qt.UserRole)
            self.metrics_model.setItem(row, 0, item)

        # self.vwMetrics.setModel(self.metrics_model)

        # for row in range(len(metrics) - 1):
        #     cbo = QtWidgets.QComboBox()
        #     cbo.addItems(['Metric', 'Indicator', 'None'])
        #     self.vwMetrics.setIndexWidget(self.metrics_model.index(row, 1), cbo)

        # self.vwMetrics.resizeColumnToContents(0)
        # self.vwMetrics.resizeColumnToContents(1)
        # self.metrics_model.setHorizontalHeaderLabels(['Metric', 'Status'])
        # self.vwMetrics.verticalHeader().hide()

        if analysis is not None:
            self.setWindowTitle('Edit Analysis Properties')

            self.txtName.setText(analysis.name)
            self.txtDescription.setPlainText(analysis.description)
            # self.chkAddToMap.setCheckState(Qt.Unchecked)
            # self.chkAddToMap.setVisible(False)

            # TODO: Set dropdowns when existing analysis

            # User cannot reassign mask once the analysis is created!
            self.cboMask.setEnabled(False)
        else:
            self.setWindowTitle('Create New Analysis')

    def setupUi(self):

        self.setMinimumSize(500, 500)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grdLayout1 = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grdLayout1)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grdLayout1.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.grdLayout1.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblMask = QtWidgets.QLabel()
        self.lblMask.setText('Mask')
        self.grdLayout1.addWidget(self.lblMask, 1, 0, 1, 1)

        self.cboMask = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboMask, 1, 1, 1, 1)

        self.lblBasemap = QtWidgets.QLabel()
        self.lblBasemap.setText('Basemap')
        self.grdLayout1.addWidget(self.lblBasemap, 2, 0, 1, 1)

        self.cboBasemap = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboBasemap, 2, 1, 1, 1)

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        self.metricsTable = QtWidgets.QTableWidget()
        self.tabWidget.addTab(self.metricsTable, 'Analysis Metrics')

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tabWidget.addTab(self.txtDescription, 'Description')

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.cmdHelp = QtWidgets.QPushButton()
        self.cmdHelp.setText('Help')
        self.horiz.addWidget(self.cmdHelp)

        self.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horiz.addItem(self.spacerItem)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.horiz.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Analysis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        mask = self.cboMask.currentData(QtCore.Qt.UserRole)
        if mask is None:
            QtWidgets.QMessageBox.warning(self, 'Missing Mask', 'You must select a mask to continue.')
            self.cboMask.setFocus()
            return()

        basemap = self.cboBasemap.currentData(QtCore.Qt.UserRole)
        if basemap is None:
            QtWidgets.QMessageBox.warning(self, 'Missing Basemap', 'You must select a basemap to continue.')
            self.cboBasemap.setFocus()
            return()

        if self.analysis is not None:
            try:
                self.analysis.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), basemap)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), mask, basemap)
                self.project.analyses[self.analysis.id] = self.analysis
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
