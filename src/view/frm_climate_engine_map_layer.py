import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate

from qgis.core import QgsApplication
from qgis.utils import iface

from .widgets.date_range import DateRangeWidget
from .utilities import add_help_button

from ..gp.download_climate_engine_task import AREA_REDUCER
from ..model.project import Project
from ..lib.climate_engine import get_datasets, get_dataset_date_range, get_raster_mapid, open_climate_engine_website


date_ranges = ['1 Year', '3 Years', '5 Years', '10 Years', 'Full Data Range', 'Custom']

class FrmClimateEngineMapLayer(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None, qris_project: Project = None, sample_frame_id: int = None, sample_frame_feature_fids: list = None):
        super().__init__(parent)

        self.iface = iface
        self.layer_geometry = None
        self.qris_project = qris_project
        self.date_range_widget = DateRangeWidget(self, horizontal=False)

        self.map_tile_url = None
        self.map_tile_layer_name = None

        self.setWindowTitle('Add Climate Engine Map Layer')
        self.setupUi()

        # Datasets
        self.datasets = {}
        datasets = get_datasets()
        for dataset_id, dataset in datasets.items():
            if dataset.get('mapping', False) is True:
                self.datasets[dataset_id] = dataset

        for dataset in self.datasets.values():
            dataset_name = dataset.get('datasetName', None)
            if len(dataset.get('variables', [])) == 0:
                continue
            self.cboDataset.addItem(dataset_name, dataset)

        self.cboDataset.setCurrentIndex(-1)
        self.cboDataset.currentIndexChanged.connect(self.on_dataset_changed)

        for area_reducer_name, area_reducer in AREA_REDUCER.items():
            self.cboStatistic.addItem(area_reducer_name, area_reducer)

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

        self.cboVariable.clear()
        self.cboVariable.setEnabled(False)

        # grab the selected dataset_info
        dataset: dict = self.cboDataset.itemData(index)
        if dataset is None:
            return
        dataset_variables = dataset.get('variables', None)
        if dataset_variables is not None and len(dataset_variables) > 0:
            for variable in dataset_variables:
                item = QtWidgets.QListWidgetItem(variable['variableName'])
                item.setData(QtCore.Qt.UserRole, variable)
                self.cboVariable.addItem(item.text(), item.data(QtCore.Qt.UserRole))
                # if variable.get('displayInQRiS', False) is False and self.chkFilterQris.isChecked():
                #     item.setHidden(True)
            self.cboVariable.setEnabled(True)
        
        date_range = get_dataset_date_range(dataset.get('datasetId', None))

        if date_range is not None:
            self.min_date = QDate().fromString(date_range.get('min', ""), 'yyyy-MM-dd')
            self.max_date = QDate().fromString(date_range.get('max', ""), 'yyyy-MM-dd')
            self.date_range_widget.set_date_range_bounds(self.min_date.toPyDate(), self.max_date.toPyDate())
            self.on_date_range_changed()

    def add_to_map(self):

        if self.cboDataset.currentIndex() == -1:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a dataset')
            return
        dataset = self.cboDataset.itemData(self.cboDataset.currentIndex())
        dataset_id = dataset.get('datasetId', None)

        if self.cboVariable.currentIndex() == -1:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one variable')
            return
        variable = self.cboVariable.itemData(self.cboVariable.currentIndex())

        # if date range is over 10 years, warn user
        if self.date_range_widget.get_date_range() is not None:
            start_date, end_date = self.date_range_widget.get_date_range()
            date_diff = end_date - start_date
            if date_diff.days > 3650:
                result = QtWidgets.QMessageBox.warning(self, 'Warning', 'The date range is over 10 years. This may take a long time to download, especially for several sample frame features. Do you want to continue?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.No:
                    return

        start_date, end_date = self.date_range_widget.get_date_range()

        if self.cboStatistic.currentIndex() == -1:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a statistic')
            return
        
        statistic = self.cboStatistic.itemData(self.cboStatistic.currentIndex())
        if statistic is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a statistic')
            return
        
        opacity = self.dblOpacity.value()
        if opacity < 0.0 or opacity > 1.0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Opacity must be between 0.0 and 1.0')
            return

        self.map_tile_url = get_raster_mapid(dataset_id, variable['variableName'], statistic, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), color_map_opacity=opacity)
        self.map_tile_layer_name = f'{dataset["datasetName"]} - {variable["variableName"]}'

        if self.map_tile_url is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Error downloading data from Climate Engine')
            return
        
        super(FrmClimateEngineMapLayer, self).accept()


    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        # self.lblName = QtWidgets.QLabel('Name')
        # self.grid.addWidget(self.lblName, 0, 0)

        # self.txtName = QtWidgets.QLineEdit()
        # self.txtName.setReadOnly(True)
        # self.grid.addWidget(self.txtName, 0, 1)

        self.lblDataset = QtWidgets.QLabel('Dataset')
        self.grid.addWidget(self.lblDataset, 1, 0)

        self.cboDataset = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboDataset, 1, 1)

        self.vert_variables = QtWidgets.QVBoxLayout()
        self.grid.addLayout(self.vert_variables, 2, 0)

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

        self.cboVariable = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboVariable, 3, 1)

        self.lblDateRange = QtWidgets.QLabel('Date Range')
        self.grid.addWidget(self.lblDateRange, 4, 0)
        # set the alignment of the label in the cell to the top
        self.grid.setAlignment(self.lblDateRange, QtCore.Qt.AlignTop)
        
        self.frameDateRange = QtWidgets.QFrame()
        self.frameDateRange.setLayout(QtWidgets.QVBoxLayout())
        self.frameDateRange.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins
        # self.frameDateRange.layout().setSpacing(0)  # Remove spacing
        self.frameDateRange.setObjectName("frameDateRange")
        self.frameDateRange.setStyleSheet('QFrame#frameDateRange {border: 1px solid gray; border-radius: 3px; padding: 5px;}')
        self.grid.addWidget(self.frameDateRange, 4, 1)
        self.grid.setAlignment(self.frameDateRange, QtCore.Qt.AlignTop)

        self.cboDateRange = QtWidgets.QComboBox()
        self.cboDateRange.addItems(date_ranges)
        self.cboDateRange.currentIndexChanged.connect(self.on_date_range_changed)
        self.frameDateRange.layout().addWidget(self.cboDateRange)

        self.date_range_widget.setEnabled(False)
        self.frameDateRange.layout().addWidget(self.date_range_widget)
        self.frameDateRange.layout().setAlignment(self.date_range_widget, QtCore.Qt.AlignTop)

        self.lblStatistic = QtWidgets.QLabel('Statistic')
        self.grid.addWidget(self.lblStatistic, 5, 0)

        self.cboStatistic = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboStatistic, 5, 1)

        self.lblOpacity = QtWidgets.QLabel('Opacity')
        self.grid.addWidget(self.lblOpacity, 6, 0)

        self.dblOpacity = QtWidgets.QDoubleSpinBox()
        self.dblOpacity.setRange(0.0, 1.0)
        self.dblOpacity.setSingleStep(0.1)
        self.dblOpacity.setValue(0.7)
        self.grid.addWidget(self.dblOpacity, 6, 1)

        # # # Adjust row stretch factors
        # self.grid.setRowStretch(0, 0)  # Decrease height of row 0
        # self.grid.setRowStretch(1, 1)  # Default stretch for row 1
        # self.grid.setRowStretch(2, 10)  # Increase height of row 2
        # self.grid.setRowStretch(3, 0)

        self.horiz_buttons = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz_buttons)

        self.btn_climate_engine = QtWidgets.QPushButton('About Climate Engine')
        self.btn_climate_engine.setStyleSheet('QPushButton {text-decoration: underline; color: blue;}')
        self.btn_climate_engine.clicked.connect(open_climate_engine_website)
        self.horiz_buttons.addWidget(self.btn_climate_engine)

        self.btnHelp = add_help_button(self, 'context/climate-engine-download')
        self.horiz_buttons.addWidget(self.btnHelp)

        self.horiz_buttons.addStretch()

        self.btnGetMapLayer = QtWidgets.QPushButton('Add to Map')
        self.btnGetMapLayer.clicked.connect(self.add_to_map)
        self.horiz_buttons.addWidget(self.btnGetMapLayer)

        self.btn_close = QtWidgets.QPushButton('Cancel')
        self.btn_close.clicked.connect(self.close)
        self.horiz_buttons.addWidget(self.btn_close)
        


