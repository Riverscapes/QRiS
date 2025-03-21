import os

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer

from ..model.analysis import Analysis, insert_analysis
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.profile import Profile
from ..model.raster import Raster
from ..model.sample_frame import SampleFrame
from ..model.analysis_metric import AnalysisMetric

from .utilities import validate_name, add_standard_form_buttons
from ..QRiS.settings import CONSTANTS


class FrmAnalysisProperties(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, analysis: Analysis = None):

        self.project = project
        self.analysis = analysis

        super(FrmAnalysisProperties, self).__init__(parent)
        self.setupUi()

        # Sample Frames
        self.sampling_frames = {id: sample_frame for id, sample_frame in project.analysis_masks().items()}
        self.sampling_frames_model = DBItemModel(self.sampling_frames)
        self.cboSampleFrame.setModel(self.sampling_frames_model)
        self.cboSampleFrame.currentIndexChanged.connect(self.on_cboSampleFrame_currentIndexChanged)

        # Valley Bottoms
        self.valley_bottoms = {id: valley_bottom for id, valley_bottom in project.valley_bottoms.items()}
        self.valley_bottoms_model = DBItemModel(self.valley_bottoms)
        self.cboValleyBottom.setModel(self.valley_bottoms_model)

        # Centerlines
        self.centerlines = {id: profile for id, profile in project.profiles.items()}
        self.centerlines_model = DBItemModel(self.centerlines)
        self.cboCenterline.setModel(self.centerlines_model)

        # DEMs
        self.dems = {id: surface for id, surface in project.rasters.items() if surface.raster_type_id == 4}
        self.dems_model = DBItemModel(self.dems)
        self.cboDEM.setModel(self.dems_model)

        metrics = list(project.metrics.values())
        self.metricsTable.setRowCount(len(metrics))

        for row in range(len(metrics)):

            level_id = metrics[row].default_level_id
            if analysis is not None:
                if metrics[row].id in analysis.analysis_metrics:
                    level_id = analysis.analysis_metrics[metrics[row].id].level_id

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

            cmdHelp = QtWidgets.QPushButton()
            cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
            cmdHelp.setToolTip('Metric Definition')
            name = metrics[row].name
            cmdHelp.clicked.connect(self.help(name))
            self.metricsTable.setCellWidget(row, 2, cmdHelp)

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
            
            # Set the sample frame
            index = self.cboSampleFrame.findData(analysis.sample_frame)
            self.cboSampleFrame.setCurrentIndex(index)

            if analysis.metadata and 'valley_bottom' in analysis.metadata:
                valley_bottom: DBItem = self.valley_bottoms[analysis.metadata['valley_bottom']]
                index = self.cboValleyBottom.findData(valley_bottom)
                self.cboValleyBottom.setCurrentIndex(index)

            # Set the centerline
            if analysis.metadata is not None and 'centerline' in analysis.metadata:
                centerline: DBItem = self.centerlines[analysis.metadata['centerline']]
                index = self.cboCenterline.findData(centerline)
                self.cboCenterline.setCurrentIndex(index)
            else:
                self.cboCenterline.setCurrentIndex(-1)
            
            # set the dem
            if analysis.metadata is not None and 'dem' in analysis.metadata:
                dem: Raster = self.dems[analysis.metadata['dem']]
                index = self.cboDEM.findData(dem)
                self.cboDEM.setCurrentIndex(index)
            else:
                self.cboDEM.setCurrentIndex(-1)

            for row in range(self.metricsTable.rowCount()):
                metric = self.metricsTable.item(row, 0).data(QtCore.Qt.UserRole)
                cboStatus: QtWidgets.QComboBox = self.metricsTable.cellWidget(row, 1)
                if metric.id in analysis.analysis_metrics:
                    cboStatus.setCurrentIndex(analysis.analysis_metrics[metric.id].level_id)
                else:
                    # set to None if not found
                    cboStatus.setCurrentIndex(0)

            # User cannot reassign mask once the analysis is created!
            self.cboSampleFrame.setEnabled(False)
            self.cboCenterline.setEnabled(False)
            self.cboDEM.setEnabled(False)
            self.cboValleyBottom.setEnabled(False)
        else:
            self.setWindowTitle('Create New Analysis')

    def help(self, metric_name):

        return lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"{CONSTANTS['webUrl'].rstrip('/')}/Technical_Reference/metrics/#{metric_name.replace(' ', '-')}"))

    def toggle_all_metrics(self, level_id: str):
            
            for row in range(self.metricsTable.rowCount()):
                cboStatus: QtWidgets.QComboBox = self.metricsTable.cellWidget(row, 1)
                # find from text
                idx = cboStatus.findText(level_id)
                cboStatus.setCurrentIndex(idx)

    def on_cboSampleFrame_currentIndexChanged(self, index):

        # if the sample frame type is Valley Bottom, then set the Valley Bottom combo box to the selected valley bottom as well, then lock that combo box. if not, then unlock the combo box
        sample_frame: SampleFrame = self.cboSampleFrame.currentData(QtCore.Qt.UserRole)
        if sample_frame is not None:
            if sample_frame.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                index = self.cboValleyBottom.findData(sample_frame)
                self.cboValleyBottom.setCurrentIndex(index)
                self.cboValleyBottom.setEnabled(False)
            else:
                self.cboValleyBottom.setEnabled(True)

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

        self.lblSampleFrame = QtWidgets.QLabel('Analysis Masks (Sample Frame)')
        self.grdLayout1.addWidget(self.lblSampleFrame, 1, 0, 1, 1)

        self.cboSampleFrame = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboSampleFrame, 1, 1, 1, 1)

        self.lblValleyBottom = QtWidgets.QLabel('Valley Bottom')
        self.grdLayout1.addWidget(self.lblValleyBottom, 2, 0, 1, 1)

        self.cboValleyBottom = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboValleyBottom, 2, 1, 1, 1)

        self.lblCenterline = QtWidgets.QLabel('Riverscape Centerline')
        self.grdLayout1.addWidget(self.lblCenterline, 3, 0, 1, 1)
        
        self.cboCenterline = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboCenterline, 3, 1, 1, 1)

        self.lblDEM = QtWidgets.QLabel('DEM')
        self.grdLayout1.addWidget(self.lblDEM, 4, 0, 1, 1)

        self.cboDEM = QtWidgets.QComboBox()
        self.grdLayout1.addWidget(self.cboDEM, 4, 1, 1, 1)

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        # Metrics and Indicators Tab
        self.metrics_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.metrics_tab, 'Metrics and Indicators')

        self.vert_metrics = QtWidgets.QVBoxLayout(self.metrics_tab)
        self.metrics_tab.setLayout(self.vert_metrics)

        self.metricsTable = QtWidgets.QTableWidget(0, 3)
        self.metricsTable.resize(500, 500)
        self.metricsTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.metricsTable.resizeColumnsToContents()
        # self.metricsTable.horizontalHeader().setStretchLastSection(True)
        self.metricsTable.setHorizontalHeaderLabels(['Metric', 'Status', None])
        header = self.metricsTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(2, 10)
        self.metricsTable.verticalHeader().setVisible(False)
        self.metricsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.vert_metrics.addWidget(self.metricsTable)

        self.horiz_metric_buttons = QtWidgets.QHBoxLayout()
        self.vert_metrics.addLayout(self.horiz_metric_buttons)
        self.horiz_metric_buttons.addStretch()

        self.lbl_metric_set_all = QtWidgets.QLabel('Set All to:')
        self.horiz_metric_buttons.addWidget(self.lbl_metric_set_all)
        self.cmd_set_all_metrics = QtWidgets.QPushButton('Metric')
        self.cmd_set_all_metrics.clicked.connect(lambda: self.toggle_all_metrics('Metric'))
        self.horiz_metric_buttons.addWidget(self.cmd_set_all_metrics)

        self.cmd_set_all_indicators = QtWidgets.QPushButton('Indicator')
        self.cmd_set_all_indicators.clicked.connect(lambda: self.toggle_all_metrics('Indicator'))
        self.horiz_metric_buttons.addWidget(self.cmd_set_all_indicators)

        self.cmd_clear_all = QtWidgets.QPushButton('None')
        self.cmd_clear_all.clicked.connect(lambda: self.toggle_all_metrics('None'))
        self.horiz_metric_buttons.addWidget(self.cmd_clear_all)

        # Description Tab
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tabWidget.addTab(self.txtDescription, 'Description')

        self.vert.addLayout(add_standard_form_buttons(self, 'analyses'))

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        sample_frame: SampleFrame = self.cboSampleFrame.currentData(QtCore.Qt.UserRole)
        if sample_frame is None:
            QtWidgets.QMessageBox.warning(self, 'Missing Sample Frame', 'You must select a sample frame to continue.')
            self.cboSampleFrame.setFocus()
            return
        
        centerline: Profile = self.cboCenterline.currentData(QtCore.Qt.UserRole)
        dem: Raster = self.cboDEM.currentData(QtCore.Qt.UserRole)
        valley_bottom: DBItem = self.cboValleyBottom.currentData(QtCore.Qt.UserRole)

        # write the profile id to the analysis and analysis metadata
        metadata = self.analysis.metadata if self.analysis is not None else {}
        if centerline is not None:
            metadata['centerline'] = centerline.id
        if dem is not None:
            metadata['dem'] = dem.id
        if valley_bottom is not None:
            metadata['valley_bottom'] = valley_bottom.id

        # determine if there are any features in the mask
        fc_path = f"{self.project.project_file}|layername={sample_frame.fc_name}|subset={sample_frame.fc_id_column_name} = {sample_frame.id}"
        temp_layer = QgsVectorLayer(fc_path, 'temp', 'ogr')
        if temp_layer.featureCount() < 1:
            QtWidgets.QMessageBox.warning(self, 'Empty Sample Frame', 'The selected sample frame does not contain any features. Please select a different sample frame.')
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
                self.analysis.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), analysis_metrics, metadata)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), sample_frame, analysis_metrics, metadata)
                self.project.analyses[self.analysis.id] = self.analysis
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
