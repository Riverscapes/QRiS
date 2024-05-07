
import json
import sqlite3
import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate

from qgis.utils import iface

from .widgets.sample_frames import SampleFrameWidget
from .utilities import add_help_button

from ..model.project import Project
from ..lib.climate_engine import get_datasets, get_dataset_variables, get_dataset_date_range, get_dataset_timeseries_polygon, open_climate_engine_website


class FrmClimateEngineDownload(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None, qris_project: Project = None):
        super().__init__(parent)

        self.iface = iface
        self.layer_geometry = None
        self.qris_project = qris_project
        self.sample_frame_widget = SampleFrameWidget(self, qris_project)

        self.setWindowTitle('Download Climate Engine Metrics')
        self.setupUi()

        # Datasets
        self.datasets = get_datasets()
        self.cboDataset.addItems(self.datasets.keys())

    def on_dataset_changed(self, index):

        self.lboxVariables.clear()
        self.lboxVariables.setEnabled(False)

        dataset = self.cboDataset.currentText()

        dataset_id = self.datasets.get(dataset)['id']
        variables = get_dataset_variables(dataset_id)

        if variables is not None:
            for variable in variables:
                item = QtWidgets.QListWidgetItem(variable)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.lboxVariables.addItem(item)
            self.lboxVariables.setEnabled(True)
        

        date_range = get_dataset_date_range(dataset_id)

        if date_range is not None:
            self.min_date = QDate().fromString(date_range.get('min', ""), 'yyyy-MM-dd')
            self.max_date = QDate().fromString(date_range.get('max', ""), 'yyyy-MM-dd')
            self.dateStartDate.setMinimumDate(self.min_date)
            self.dateEndDate.setMinimumDate(self.min_date)
            self.dateStartDate.setMaximumDate(self.max_date)
            self.dateEndDate.setMaximumDate(self.max_date)
            self.dateStartDate.setDate(self.min_date)
            self.dateEndDate.setDate(self.max_date)
            self.dateStartDate.setEnabled(True)
            self.dateEndDate.setEnabled(True)
        else:
            self.dateStartDate.setDate(QDate())
            self.dateEndDate.setDate(QDate())
            self.dateStartDate.setEnabled(False)
            self.dateEndDate.setEnabled(False)

        self.btnGetTimeseries.setEnabled(True)


    def retrieve_timeseries(self):

        if self.sample_frame_widget.selected_sample_frame() is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a sample frame')
            return

        if self.sample_frame_widget.selected_features_count() == 0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one sample frame')
            return

        if self.lboxVariables.count() == 0:
            return

        variables = []
        for i in range(self.lboxVariables.count()):
            item = self.lboxVariables.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                variables.append(item.text())
        
        if len(variables) == 0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one variable')
            return

        dataset = self.datasets.get(self.cboDataset.currentText())['id']

        start_date = self.dateStartDate.date().toString('yyyy-MM-dd')
        end_date = self.dateEndDate.date().toString('yyyy-MM-dd')

        status = True

        time_series_ids = {}

        for feature in self.sample_frame_widget.get_selected_sample_frame_features():
            geometry = feature.geometry()
            feature_id = feature.id()

            result = get_dataset_timeseries_polygon(dataset, variables, start_date, end_date, geometry)        

            if result is None:
                status = False
                continue

            [timeseries] = result
            data = timeseries.get('Data', None)

            if data is None:
                status = False
                continue

            df = pd.DataFrame(data)

            with sqlite3.connect(self.qris_project.project_file) as conn:
                cursor = conn.cursor()
                
                for column in df.columns:
                    if column == 'Date':
                        continue
                    variable, units = column.split(' (')
                    units = units.replace(')', '')
                    df_values = df[['Date', column]]
                    df_values = df_values.set_index('Date')
                    values = list(df_values.itertuples(name=None))
                    name = f'{dataset} {variable}'
                    if name in time_series_ids:
                        time_series_id = time_series_ids[name]
                    else:   
                        metadata = {'units': units, 'start_date': start_date, 'end_date': end_date}
                        metadata_json = json.dumps(metadata)
                        cursor.execute('INSERT INTO time_series (name, source, url, metadata) VALUES (?, ?, ?, ?)', (name, 'Climate Engine', 'https://www.climateengine.org/', metadata_json))
                        time_series_id = cursor.lastrowid
                        time_series_ids[name] = time_series_id

                    cursor.executemany('INSERT INTO sample_frame_time_series (sample_frame_fid, time_series_id, time_value, value) VALUES (?, ?, ?, ?)', [(feature_id, time_series_id, date, value) for date, value in values])

        if status is True:
            self.lblStatus.setText('Timeseries retrieved successfully')
            QtWidgets.QMessageBox.information(self, 'Climate Engine Download', 'Climate Engine Timeseries retrieved successfully')
            self.btn_close.setText('Close')
            self.btnGetTimeseries.setEnabled(False)
        else:
            self.lblStatus.setText('Error retrieving timeseries')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblSampleFrames = QtWidgets.QLabel('Sample Frames')
        self.grid.addWidget(self.lblSampleFrames, 0, 0)

        self.grid.addWidget(self.sample_frame_widget, 0, 1)

        self.lblDataset = QtWidgets.QLabel('Dataset')
        self.grid.addWidget(self.lblDataset, 1, 0)

        self.cboDataset = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboDataset, 1, 1)

        self.lblVariable = QtWidgets.QLabel('Variables')
        self.grid.addWidget(self.lblVariable, 2, 0)

        self.lboxVariables = QtWidgets.QListWidget()
        self.grid.addWidget(self.lboxVariables, 2, 1)

        self.lblStartDate = QtWidgets.QLabel('Start Date')
        self.grid.addWidget(self.lblStartDate, 3, 0)

        self.dateStartDate = QtWidgets.QDateEdit()
        self.grid.addWidget(self.dateStartDate, 3, 1)
        self.dateStartDate.setEnabled(False)

        self.lblEndDate = QtWidgets.QLabel('End Date')
        self.grid.addWidget(self.lblEndDate, 4, 0)

        self.dateEndDate = QtWidgets.QDateEdit()
        self.grid.addWidget(self.dateEndDate, 4, 1)
        self.dateEndDate.setEnabled(False)

        self.horiz_buttons = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz_buttons)

        self.btn_climate_engine = QtWidgets.QPushButton('Climate Engine')
        self.btn_climate_engine.setStyleSheet('QPushButton {text-decoration: underline; color: blue;}')
        self.btn_climate_engine.clicked.connect(open_climate_engine_website)
        self.horiz_buttons.addWidget(self.btn_climate_engine)

        self.btnHelp = add_help_button(self, 'context/climate-engine-download')
        self.horiz_buttons.addWidget(self.btnHelp)

        self.horiz_buttons.addStretch()

        self.btnGetTimeseries = QtWidgets.QPushButton('Get Timeseries')
        self.btnGetTimeseries.clicked.connect(self.retrieve_timeseries)
        self.horiz_buttons.addWidget(self.btnGetTimeseries)
        self.btnGetTimeseries.setEnabled(False)

        self.btn_close = QtWidgets.QPushButton('Cancel')
        self.btn_close.clicked.connect(self.close)
        self.horiz_buttons.addWidget(self.btn_close)

        self.lblStatus = QtWidgets.QLabel()
        self.vert.addWidget(self.lblStatus)
        
        self.cboDataset.currentIndexChanged.connect(self.on_dataset_changed)

