import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate

from qgis.core import QgsApplication
from qgis.utils import iface

from .widgets.sample_frames import SampleFrameWidget
from .widgets.date_range import DateRangeWidget
from .utilities import add_help_button

from ..gp.download_climate_engine_task import AREA_REDUCER, DownloadClimateEngineTimeseriesTask
from ..model.project import Project
from ..model.sample_frame import SampleFrame
from ..lib.climate_engine import get_datasets, get_dataset_date_range, get_dataset_timeseries_polygon, open_climate_engine_website


date_ranges = ['1 Year', '3 Years', '5 Years', '10 Years', 'Full Data Range', 'Custom']

class FrmClimateEngineDownload(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None, qris_project: Project = None, sample_frame_id: int = None, sample_frame_feature_fids: list = None):
        super().__init__(parent)

        self.iface = iface
        self.layer_geometry = None
        self.qris_project = qris_project
        self.sample_frame_widget = SampleFrameWidget(self, qris_project, sample_frame_types=[SampleFrame.AOI_SAMPLE_FRAME_TYPE, SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE, SampleFrame.SAMPLE_FRAME_TYPE])
        self.date_range_widget = DateRangeWidget(self, horizontal=False)

        self.setWindowTitle('Download Climate Engine Timeseries')
        self.setupUi()

        # Datasets
        datasets = get_datasets()
        for dataset in datasets.values():
            variables = dataset.get('variables', [])
            if len(variables) == 0:
                continue
            self.cboDataset.addItem(dataset.get('datasetName', '-Unknown Dataset Name-'), dataset)

        self.cboDataset.setCurrentIndex(-1)

        if sample_frame_id is not None:
            self.sample_frame_widget.set_selected_sample_frame(sample_frame_id, sample_frame_feature_fids)

        for area_reducer_name, area_reducer in AREA_REDUCER.items():
            self.cboAreaReducer.addItem(area_reducer_name, area_reducer)

    def on_date_range_changed(self):
            
            date_range = self.cboDateRange.currentText()
    
            if date_range == '1 Year':
                self.date_range_widget.set_dates(self.max_date.addYears(-1).toPyDate(), self.max_date.toPyDate())
            elif date_range == '3 Years':
                self.date_range_widget.set_dates(self.max_date.addYears(-3).toPyDate(), self.max_date.toPyDate())
            elif date_range == '5 Years':
                self.date_range_widget.set_dates(self.max_date.addYears(-5).toPyDate(), self.max_date.toPyDate())
            elif date_range == '10 Years':
                self.date_range_widget.set_dates(self.max_date.addYears(-10).toPyDate(), self.max_date.toPyDate())
            elif date_range == 'Full Data Range':
                self.date_range_widget.set_dates_to_bounds()
            elif date_range == 'Custom':
                self.date_range_widget.setEnabled(True)
                return
    
            self.date_range_widget.setEnabled(False)

    def on_dataset_changed(self, index):

        self.lboxVariables.clear()
        self.lboxVariables.setEnabled(False)

        # grab the selected dataset_info
        dataset: dict = self.cboDataset.itemData(index)
        if dataset is None:
            return
        dataset_variables = dataset.get('variables', None)
        if dataset_variables is not None and len(dataset_variables) > 0:
            for variable in dataset_variables:
                item = QtWidgets.QListWidgetItem(variable['variableName'])
                item.setData(QtCore.Qt.UserRole, variable)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.lboxVariables.addItem(item)
                if variable.get('defaultVisible', False) is False and self.chkFilterQris.isChecked():
                    item.setHidden(True)
            self.lboxVariables.setEnabled(True)
        
        date_range = get_dataset_date_range(dataset.get('dataseItd', None))

        if date_range is not None:
            self.min_date = QDate().fromString(date_range.get('min', ""), 'yyyy-MM-dd')
            self.max_date = QDate().fromString(date_range.get('max', ""), 'yyyy-MM-dd')
            self.date_range_widget.set_date_range_bounds(self.min_date.toPyDate(), self.max_date.toPyDate())
            self.on_date_range_changed()

        self.btnGetTimeseries.setEnabled(True)

    def on_chkFilterQris(self, state):

        # desired behavior is to filter the list of variables to those that are in the QRIS project. things to consider:

        if state == QtCore.Qt.Checked:
            # filter the list of variables to those that are in the QRIS project
            for i in range(self.lboxVariables.count()):
                item = self.lboxVariables.item(i)
                variable = item.data(QtCore.Qt.UserRole)
                if variable is not None:
                    if variable.get('defaultVisible', False) is False:
                        item.setHidden(True)
                    else:
                        item.setHidden(False)
            # if no variables are defaultVisible for a particular dataset, make it hidden in the combo box. Is this possible? Only for Qt 5.10+
            # for i in range(self.cboDataset.count()):
            #     item = self.cboDataset.itemData(i)
            #     if item is not None:
            #         variables = item.get('variables', [])
            #         if not any(var.get('defaultVisible', False) for var in variables):
            #             self.cboDataset.setItemHidden(i, True)
            #         else:
            #             self.cboDataset.setItemHidden(i, False)
        else:
            # show all variables
            for i in range(self.lboxVariables.count()):
                item = self.lboxVariables.item(i)
                item.setHidden(False)
            # for i in range(self.cboDataset.count()):
            #     item = self.cboDataset.itemData(i)
            #     if item is not None:
            #         self.cboDataset.setItemHidden(i, False)

    def retrieve_timeseries(self):

        if self.txtName.text() == '':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Enter a name for the timeseries')
            return

        if self.sample_frame_widget.selected_sample_frame() is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a sample frame')
            return

        if self.sample_frame_widget.selected_features_count() == 0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one sample frame')
            return

        if self.lboxVariables.count() == 0:
            return

        # if date range is over 10 years, warn user
        if self.date_range_widget.get_date_range() is not None:
            start_date, end_date = self.date_range_widget.get_date_range()
            date_diff = end_date - start_date
            if date_diff.days > 3650:
                result = QtWidgets.QMessageBox.warning(self, 'Warning', 'The date range is over 10 years. This may take a long time to download, especially for several sample frame features. Do you want to continue?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.No:
                    return

        self.lblStatus.setText('Starting Metric Download...')

        variables = []
        for i in range(self.lboxVariables.count()):
            item = self.lboxVariables.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                variable = item.data(QtCore.Qt.UserRole)
                if variable is not None:
                    variables.append(variable['variableName'])
        
        if len(variables) == 0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one variable')
            return

        name = self.txtName.text()
        dataset = self.cboDataset.itemData(self.cboDataset.currentIndex())
        if dataset is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a dataset')
            return
        dataset_id = dataset.get('datasetId', None)
        start_date, end_date = self.date_range_widget.get_date_range()

        features = list(self.sample_frame_widget.get_selected_sample_frame_features())

        area_reducer = self.cboAreaReducer.itemData(self.cboAreaReducer.currentIndex())

        task = DownloadClimateEngineTimeseriesTask(self.qris_project, name, dataset_id, variables, start_date, end_date, features, area_reducer)
        # DEBUG
        status = task.run()
        self.on_download_complete(status)
        # PRODUCTION
        # task.download_complete.connect(self.on_download_complete)
        # QgsApplication.taskManager().addTask(task)
        

    def on_download_complete(self, status):
        if status is True:
            self.lblStatus.setText('Timeseries retrieved successfully')
            QtWidgets.QMessageBox.information(self, 'Climate Engine Download', 'Climate Engine Timeseries retrieved successfully')
            self.btn_close.setText('Close')
            if self.chkCloseWindow.isChecked():
                self.close()
        else:
            self.lblStatus.setText('Error retrieving timeseries')


    def setupUi(self):

        self.resize(500, 750)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel('Name')
        self.grid.addWidget(self.lblName, 0, 0)

        self.txtName = QtWidgets.QLineEdit()
        self.grid.addWidget(self.txtName, 0, 1)

        self.lblSampleFrames = QtWidgets.QLabel('Sample Frames')
        self.lblSampleFrames.setAlignment(QtCore.Qt.AlignTop)
        self.grid.addWidget(self.lblSampleFrames, 1, 0)

        self.grid.addWidget(self.sample_frame_widget, 1, 1)

        self.lblDataset = QtWidgets.QLabel('Dataset')
        self.grid.addWidget(self.lblDataset, 2, 0)

        self.cboDataset = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboDataset, 2, 1)

        self.vert_variables = QtWidgets.QVBoxLayout()
        self.grid.addLayout(self.vert_variables, 3, 0)

        self.lblVariable = QtWidgets.QLabel('Variables')
        self.lblVariable.setAlignment(QtCore.Qt.AlignTop)
        self.vert_variables.addWidget(self.lblVariable)

        self.btn_variable_description = QtWidgets.QPushButton()
        icon = QtGui.QIcon(':/plugins/qris_toolbar/help')
        self.btn_variable_description.setIcon(icon)
        self.btn_variable_description.setIconSize(QtCore.QSize(16, 16))
        self.btn_variable_description.setFixedSize(24, 24)
        self.btn_variable_description.clicked.connect(lambda: webbrowser.open('https://docs.climateengine.org/docs/build/html/variables.html'))
        self.btn_variable_description.setToolTip('Climate Engine Variable Descriptions')
        self.vert_variables.addWidget(self.btn_variable_description)
        self.vert_variables.addStretch() 

        self.lboxVariables = QtWidgets.QListWidget()
        self.lboxVariables.setMinimumHeight(200)
        self.grid.addWidget(self.lboxVariables, 3, 1)

        self.chkFilterQris = QtWidgets.QCheckBox('Filter Variables to QRIS')
        self.chkFilterQris.setChecked(True)
        self.chkFilterQris.setToolTip('Filter variables to those available in QRIS')
        self.chkFilterQris.stateChanged.connect(self.on_chkFilterQris)
        self.grid.addWidget(self.chkFilterQris, 4, 1)

        self.lblDateRange = QtWidgets.QLabel('Date Range')
        self.grid.addWidget(self.lblDateRange, 5, 0)
        # set the alignment of the label in the cell to the top
        self.grid.setAlignment(self.lblDateRange, QtCore.Qt.AlignTop)
        
        self.frameDateRange = QtWidgets.QFrame()
        self.frameDateRange.setLayout(QtWidgets.QVBoxLayout())
        self.frameDateRange.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins
        # self.frameDateRange.layout().setSpacing(0)  # Remove spacing
        self.frameDateRange.setObjectName("frameDateRange")
        self.frameDateRange.setStyleSheet('QFrame#frameDateRange {border: 1px solid gray; border-radius: 3px; padding: 5px;}')
        self.grid.addWidget(self.frameDateRange, 5, 1)
        self.grid.setAlignment(self.frameDateRange, QtCore.Qt.AlignTop)

        self.cboDateRange = QtWidgets.QComboBox()
        self.cboDateRange.addItems(date_ranges)
        self.cboDateRange.currentIndexChanged.connect(self.on_date_range_changed)
        self.frameDateRange.layout().addWidget(self.cboDateRange)

        self.date_range_widget.setEnabled(False)
        self.frameDateRange.layout().addWidget(self.date_range_widget)
        self.frameDateRange.layout().setAlignment(self.date_range_widget, QtCore.Qt.AlignTop)

        self.lblAreaReducer = QtWidgets.QLabel('Area Reducer')
        self.grid.addWidget(self.lblAreaReducer, 7, 0)

        self.cboAreaReducer = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboAreaReducer, 7, 1)

        # # Adjust row stretch factors
        self.grid.setRowStretch(0, 0)  # Decrease height of row 0
        self.grid.setRowStretch(1, 1)  # Default stretch for row 1
        self.grid.setRowStretch(2, 10)  # Increase height of row 2
        self.grid.setRowStretch(3, 0)

        self.chkCloseWindow = QtWidgets.QCheckBox('Close Window Open After Download')
        self.chkCloseWindow.setChecked(True)
        self.grid.addWidget(self.chkCloseWindow, 8, 1, 1, 2)

        self.lblStatus = QtWidgets.QLabel("Select sample frames, dataset, variables, and the date range. Then Click 'Download Timeseries'.")
        self.vert.addWidget(self.lblStatus)

        self.horiz_buttons = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz_buttons)

        self.btn_climate_engine = QtWidgets.QPushButton('About Climate Engine')
        self.btn_climate_engine.setStyleSheet('QPushButton {text-decoration: underline; color: blue;}')
        self.btn_climate_engine.clicked.connect(open_climate_engine_website)
        self.horiz_buttons.addWidget(self.btn_climate_engine)

        self.btnHelp = add_help_button(self, 'context/climate-engine-download')
        self.horiz_buttons.addWidget(self.btnHelp)

        self.horiz_buttons.addStretch()

        self.btnGetTimeseries = QtWidgets.QPushButton('Download Timeseries')
        self.btnGetTimeseries.clicked.connect(self.retrieve_timeseries)
        self.horiz_buttons.addWidget(self.btnGetTimeseries)
        self.btnGetTimeseries.setEnabled(False)

        self.btn_close = QtWidgets.QPushButton('Cancel')
        self.btn_close.clicked.connect(self.close)
        self.horiz_buttons.addWidget(self.btn_close)
        
        self.cboDataset.currentIndexChanged.connect(self.on_dataset_changed)

