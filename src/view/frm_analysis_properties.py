import os

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis import core, gui, utils

from ..model.analysis import Analysis, insert_analysis
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import REGULAR_MASK_TYPE_ID
from ..model.analysis_metric import AnalysisMetric
from .utilities import validate_name, add_standard_form_buttons


class FrmAnalysisProperties(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, analysis: Analysis = None):

        self.project = project
        self.analysis = analysis

        super(FrmAnalysisProperties, self).__init__(parent)
        self.setupUi()

        # Masks (filtered to just regular masks )
        self.sampling_frames = {id: mask for id, mask in project.masks.items() if mask.mask_type.id == REGULAR_MASK_TYPE_ID}
        self.sampling_frames_model = DBItemModel(self.sampling_frames)
        self.cboSampleFrame.setModel(self.sampling_frames_model)

        # self.metrics_model = QtGui.QStandardItemModel(len(project.metrics), 2)
        metrics = list(project.metrics.values())
        self.metricsTable.setRowCount(len(metrics))
        # self.metricsTable.setColumnCount(2)

        for row in range(len(metrics)):

            level_id = metrics[row].default_level_id
            if analysis is not None:
                print('TODO: load initial metric state from analysis')

            label_item = QtWidgets.QTableWidgetItem()
            label_item.setText(metrics[row].name)
            self.metricsTable.setItem(row, 0, label_item)
            label_item.setData(QtCore.Qt.UserRole, metrics[row])
            label_item.setFlags(QtCore.Qt.ItemIsEnabled)

            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            self.metricsTable.setCellWidget(row, 1, cboStatus)

        self.metricsTable.setColumnWidth(0, self.metricsTable.width() / 2)
        self.metricsTable.setColumnWidth(1, self.metricsTable.width() / 2)

        # https://wiki.qt.io/How_to_Use_QTableWidget
        # m_pTableWidget -> setEditTriggers(QAbstractItemView: : NoEditTriggers);
        # m_pTableWidget -> setSelectionMode(QAbstractItemView: : SingleSelection);
        # m_pTableWidget -> setShowGrid(false);
        # m_pTableWidget -> setStyleSheet("QTableView {selection-background-color: red;}");
        # m_pTableWidget -> setGeometry(QApplication: : desktop() -> screenGeometry());

        if analysis is not None:
            self.setWindowTitle('Edit Analysis Properties')

            self.txtName.setText(analysis.name)
            self.txtDescription.setPlainText(analysis.description)
            # self.chkAddToMap.setCheckState(Qt.Unchecked)
            # self.chkAddToMap.setVisible(False)

            # TODO: Set dropdowns when existing analysis

            # User cannot reassign mask once the analysis is created!
            self.cboSampleFrame.setEnabled(False)
        else:
            self.setWindowTitle('Create New Analysis')

    def setupUi(self):

        self.setMinimumSize(500, 500)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grdLayout1 = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grdLayout1)

        self.lblName = QtWidgets.QLabel('Name')
        self.grdLayout1.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.grdLayout1.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblSampleFrame = QtWidgets.QLabel('Sample Frame')
        self.grdLayout1.addWidget(self.lblSampleFrame, 1, 0, 1, 1)

        self.cboSampleFrame = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboSampleFrame, 1, 1, 1, 1)

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        self.metricsTable = QtWidgets.QTableWidget(0, 2)
        self.tabWidget.addTab(self.metricsTable, 'Metrics and Indicators')
        # self.metricsTable.horizontalHeader().setStretchLastSection(True)
        self.metricsTable.setHorizontalHeaderLabels(['Metric', 'Status'])

        self.metricsTable.verticalHeader().setVisible(False)
        self.metricsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tabWidget.addTab(self.txtDescription, 'Description')

        self.vert.addLayout(add_standard_form_buttons(self, 'analysis'))

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        mask = self.cboSampleFrame.currentData(QtCore.Qt.UserRole)
        if mask is None:
            QtWidgets.QMessageBox.warning(self, 'Missing Mask', 'You must select a mask to continue.')
            self.cboSampleFrame.setFocus()
            return

        # Must include at least one metric!
        analysis_metrics = {}
        for row in range(self.metricsTable.rowCount()):
            metric = self.metricsTable.item(row, 0).data(QtCore.Qt.UserRole)
            cboStatus = self.metricsTable.cellWidget(row, 1)
            level_id = cboStatus.currentData(QtCore.Qt.UserRole)
            if level_id > 0:
                analysis_metrics[metric.id] = AnalysisMetric(metric, level_id)

        if len(analysis_metrics) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Metric', 'You must include at least one metric to continue.')
            self.metricsTable.setFocus()
            return

        if self.analysis is not None:
            try:
                self.analysis.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), analysis_metrics)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), mask, analysis_metrics)
                self.project.analyses[self.analysis.id] = self.analysis
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
