import os

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis import core, gui, utils

from ..model.analysis import Analysis, insert_analysis
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

        # self.metrics_model = QtGui.QStandardItemModel(len(project.metrics), 2)
        metrics = list(project.metrics.values())
        self.metricsTable.setRowCount(len(metrics))
        # self.metricsTable.setColumnCount(2)

        for row in range(len(metrics)):
            label_item = QtWidgets.QTableWidgetItem()
            label_item.setText(metrics[row].name)
            self.metricsTable.setItem(row, 0, label_item)
            label_item.setData(QtCore.Qt.UserRole, metrics[row])
            label_item.setFlags(QtCore.Qt.ItemIsEnabled)

            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
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

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        self.metricsTable = QtWidgets.QTableWidget(0, 2)
        self.tabWidget.addTab(self.metricsTable, 'Analysis Metrics')
        self.metricsTable.horizontalHeader().setStretchLastSection(True)
        self.metricsTable.setHorizontalHeaderLabels(['Metric', 'Status'])

        self.metricsTable.verticalHeader().setVisible(False)
        self.metricsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

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
            QtWidgets.QMessageBox.warning(self, 'Missing Analysis Name', 'You must provide an analysis name to continue.')
            self.txtName.setFocus()
            return()

        mask = self.cboMask.currentData(QtCore.Qt.UserRole)
        if mask is None:
            QtWidgets.QMessageBox.warning(self, 'Missing Mask', 'You must select a mask to continue.')
            self.cboMask.setFocus()
            return()

        if self.analysis is not None:
            try:
                self.analysis.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), mask)
                self.project.analyses[self.analysis.id] = self.analysis
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
