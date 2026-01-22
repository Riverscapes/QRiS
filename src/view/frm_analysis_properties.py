import os

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer

from ..model.analysis import Analysis, insert_analysis
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.profile import Profile
from ..model.raster import Raster
from ..model.sample_frame import SampleFrame
from ..model.metric import Metric
from ..model.analysis_metric import AnalysisMetric

from .frm_layer_metric_details import FrmLayerMetricDetails
from .frm_layer_metric_details import FrmLayerMetricDetails
from .widgets.metric_selector_stacked import MetricSelector
from .utilities import validate_name, add_standard_form_buttons
from ..QRiS.settings import CONSTANTS

class FrmAnalysisProperties(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, analysis: Analysis = None):

        super(FrmAnalysisProperties, self).__init__(parent)
        
        self.qris_project = qris_project
        self.analysis = analysis
        self.metric_selector = MetricSelector(self, self.qris_project, self.analysis)
        
        self.setupUi()

        # Sample Frames
        self.sampling_frames = {id: sample_frame for id, sample_frame in self.qris_project.analysis_masks().items()}
        self.sampling_frames_model = DBItemModel(self.sampling_frames)
        self.cboSampleFrame.setModel(self.sampling_frames_model)
        self.cboSampleFrame.currentIndexChanged.connect(self.on_cboSampleFrame_currentIndexChanged)

        # Valley Bottoms
        self.valley_bottoms = {id: valley_bottom for id, valley_bottom in self.qris_project.valley_bottoms.items()}
        self.valley_bottoms_model = DBItemModel(self.valley_bottoms)
        self.cboValleyBottom.setModel(self.valley_bottoms_model)

        # Centerlines
        self.centerlines = {id: profile for id, profile in self.qris_project.profiles.items()}
        self.centerlines_model = DBItemModel(self.centerlines)
        self.cboCenterline.setModel(self.centerlines_model)

        # DEMs
        self.dems = {id: surface for id, surface in self.qris_project.rasters.items() if surface.raster_type_id == 4}
        self.dems_model = DBItemModel(self.dems)
        self.cboDEM.setModel(self.dems_model)

        if analysis is not None:
            self.setWindowTitle('Edit Analysis Properties')

            self.txtName.setText(analysis.name)
            self.txtDescription.setPlainText(analysis.description)
            
            # Set the sample frame
            index = self.cboSampleFrame.findData(analysis.sample_frame)
            self.cboSampleFrame.setCurrentIndex(index)

            self.cboValleyBottom.setCurrentIndex(-1)
            self.cboCenterline.setCurrentIndex(-1)
            self.cboDEM.setCurrentIndex(-1)

            if analysis.metadata is not None:
                # Set the valley bottom
                analysis_valley_bottom = analysis.metadata.get('valley_bottom', None)
                if analysis_valley_bottom is not None:
                    valley_bottom: DBItem = self.valley_bottoms[analysis_valley_bottom]
                    index = self.cboValleyBottom.findData(valley_bottom)
                    self.cboValleyBottom.setCurrentIndex(index)
                # Set the centerline
                anaysis_centerline = analysis.metadata.get('centerline', None)
                if anaysis_centerline is not None:
                    centerline: Profile = self.centerlines[anaysis_centerline]
                    index = self.cboCenterline.findData(centerline)
                    self.cboCenterline.setCurrentIndex(index)
                # set the dem
                analysis_dem = analysis.metadata.get('dem', None)
                if analysis_dem is not None:
                    dem: Raster = self.dems[analysis_dem]
                    index = self.cboDEM.findData(dem)
                    self.cboDEM.setCurrentIndex(index)

            # User cannot reassign mask once the analysis is created!
            self.cboSampleFrame.setEnabled(False)
            self.cboCenterline.setEnabled(False)
            self.cboDEM.setEnabled(False)
            self.cboValleyBottom.setEnabled(False)
        else:
            self.setWindowTitle('Create New Analysis')

    def help(self, metric: Metric):

        return 
        # return lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"{CONSTANTS['webUrl'].rstrip('/')}/Technical_Reference/metrics/#{metric_name.replace(' ', '-')}"))

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
        
        self.vert_metrics.addWidget(self.metric_selector)

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
        fc_path = f"{self.qris_project.project_file}|layername={sample_frame.fc_name}|subset={sample_frame.fc_id_column_name} = {sample_frame.id}"
        temp_layer = QgsVectorLayer(fc_path, 'temp', 'ogr')
        if temp_layer.featureCount() < 1:
            QtWidgets.QMessageBox.warning(self, 'Empty Sample Frame', 'The selected sample frame does not contain any features. Please select a different sample frame.')
            self.cboSampleFrame.setFocus()
            return

        # Must include at least one metric!
        analysis_metrics = self.metric_selector.get_selected_metrics()
        # analysis_metrics = {}
        # for row in range(self.metricsTable.rowCount()):
        #     metric = self.metricsTable.item(row, 0).data(QtCore.Qt.UserRole)
        #     cboStatus = self.metricsTable.cellWidget(row, 1)
        #     level_id = cboStatus.currentData(QtCore.Qt.UserRole)
        #     if level_id > 0:
        #         analysis_metrics[metric.id] = AnalysisMetric(metric, level_id)

        if len(analysis_metrics) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Metric', 'You must include at least one metric to continue.')
            self.metric_selector.setFocus()
            return

        if self.analysis is not None:
            try:
                self.analysis.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), analysis_metrics, metadata)
                self.qris_project.project_changed.emit()
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), sample_frame, analysis_metrics, metadata)
                self.qris_project.add_db_item(self.analysis)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
