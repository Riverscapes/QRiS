import json
import sqlite3
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from .frm_climate_engine_download import FrmClimateEngineDownload
from .utilities import add_help_button
from .widgets.sample_frames import SampleFrameWidget
from .widgets.date_range import DateRangeWidget
from ..model.project import Project
from ..lib.climate_engine import get_datasets, open_climate_engine_website

from ..QRiS.qris_map_manager import QRisMapManager

class FrmClimateEngineExplorer(QtWidgets.QDockWidget):

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, qris_map_manager: QRisMapManager):

        super().__init__(parent)

        self.qris_project = qris_project
        self.qris_map_manager = qris_map_manager
        self.datasets = get_datasets()

        self.sample_frame_widget = SampleFrameWidget(self, self.qris_project)
        self.sample_frame_widget.cbo_sample_frame.currentIndexChanged.connect(self.load_climate_engine_metrics)
        self.sample_frame_widget.sample_frame_changed.connect(self.create_plot)

        self.date_range_widget = DateRangeWidget(self)
        self.date_range_widget.date_range_changed.connect(self.create_plot)

        self.setWindowTitle('Climate Engine Explorer')
        self.setupUi()

        self.load_climate_engine_metrics()

    def set_date_range(self):

        # need to get the date range for the selected time series
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            return
        time_series_id = time_series_ids[0].data(Qt.UserRole)

        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('SELECT * FROM time_series WHERE time_series_id = ?', (time_series_id,))
            time_series = curs.fetchone()
            metadata = json.loads(time_series[5])
            start_date = datetime.strptime(metadata['start_date'], '%Y-%m-%d') if 'start_date' in metadata else None
            end_date = datetime.strptime(metadata['end_date'], '%Y-%m-%d') if 'end_date' in metadata else None

        if start_date is not None and end_date is not None:
            self.date_range_widget.set_date_range_bounds(start_date, end_date)

    def load_climate_engine_metrics(self):
            
        # clear the list view
        self.lst_climate_engine.setModel(None)

        # get a list of the checked sample frame feature ids from the list view
        sample_frame_features = []
        for i in range(self.sample_frame_widget.sample_frames_model.rowCount(None)):
            index = self.sample_frame_widget.sample_frames_model.index(i)
            # if self.sample_frames_model.data(index, Qt.CheckStateRole) == Qt.Checked:
            sample_frame_features.append(self.sample_frame_widget.sample_frames_model.data(index, Qt.UserRole))
        if len(sample_frame_features) == 0:
            return
        sample_frame_feature_ids = [feature.id for feature in sample_frame_features]
        # get a list of the time series ids for the selected sample frame features
        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            placeholders = ', '.join('?' for _ in sample_frame_feature_ids)
            curs.execute(f'SELECT DISTINCT(time_series_id) FROM sample_frame_time_series WHERE sample_frame_fid IN ({placeholders})', sample_frame_feature_ids)
            time_series_ids = curs.fetchall()
            if len(time_series_ids) == 0:
                return
            time_series_ids = [time_series_id[0] for time_series_id in time_series_ids]
            placeholders = ', '.join('?' for _ in time_series_ids)
            curs.execute(f'SELECT time_series_id, name FROM time_series WHERE time_series_id IN ({placeholders})', time_series_ids)
            time_series_rows = curs.fetchall()

        # load the time series names into the list view
        self.time_series_model = QStandardItemModel()
        for row in time_series_rows:
            # the name should be the display, the time series id should be the data
            item = QStandardItem(row[1])
            item.setData(row[0], Qt.UserRole)
            self.time_series_model.appendRow(item)
        self.lst_climate_engine.setModel(self.time_series_model)
        self.lst_climate_engine.selectionModel().selectionChanged.connect(self.set_date_range)
        self.lst_climate_engine.selectionModel().selectionChanged.connect(self.create_plot)
        self.lst_climate_engine.update()

    def date_range_changed(self):

        self.create_plot()

    def create_plot(self):

        self._static_ax.clear()

        # get the selected time series ids
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            return
        time_series_id = time_series_ids[0].data(Qt.UserRole)

        # get the date range
        start_date, end_date = self.date_range_widget.get_date_range()

        # get the data for the selected time series
        data = {}
        # need to grab the data for each checked sample frame feature
        sample_frame_feature_ids = []
        for i in range(self.sample_frame_widget.sample_frames_model.rowCount(None)):
            index = self.sample_frame_widget.sample_frames_model.index(i)
            if self.sample_frame_widget.sample_frames_model.data(index, Qt.CheckStateRole) == Qt.Checked:
                sample_frame_feature_ids.append(self.sample_frame_widget.sample_frames_model.data(index, Qt.UserRole).id)
        
        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('SELECT * FROM time_series WHERE time_series_id = ?', (time_series_id,))
            time_series = curs.fetchone()
            time_series_name = time_series[1]
            dataset_id, variable_id = time_series_name.split(' ')
            dataset_name = next((key for key, dataset in self.datasets.items() if dataset['id'] == dataset_id), None)
            metadata = json.loads(time_series[5])
            y_label = metadata['units'] if 'units' in metadata else 'Value'
            for sample_frame_feature_id in sample_frame_feature_ids:
                curs.execute('SELECT time_value, value FROM sample_frame_time_series WHERE time_series_id = ? AND sample_frame_fid = ? AND time_value BETWEEN ? AND ?',
                             (time_series_id, sample_frame_feature_id, start_date, end_date))
                data[sample_frame_feature_id] = [(datetime.strptime(row[0], '%Y-%m-%d'), row[1]) for row in curs.fetchall()]

        # create the plot
        self._static_ax.set_xlabel('Date')
        self._static_ax.set_title(f'{dataset_name} ({variable_id})')
        if self.rdo_space.isChecked():
            for sample_frame_feature_id, values in data.items():
                self._static_ax.plot([value[0] for value in values], [value[1] for value in values], label=sample_frame_feature_id)
            self._static_ax.legend(title='Sample Frame Feature')
        elif self.rdo_time.isChecked():
            for sample_frame_feature_id, values in data.items():
                self._static_ax.plot([value[0] for value in values], [value[1] for value in values], label=sample_frame_feature_id)
            self._static_ax.legend(title='Sample Frame Feature')
        self._static_ax.set_ylabel(y_label)
        # Set the major locator to month and the major formatter to 'Month Year'
        # self._static_ax.xaxis.set_major_locator(mdates.MonthLocator())
        # self._static_ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

        # # Set the minor locator to day, but don't set a formatter so the minor ticks won't be labeled
        # self._static_ax.xaxis.set_minor_locator(mdates.DayLocator())

        # self._static_ax.xaxis.set_tick_params(rotation=45)
        # self._static_ax.grid(True)
        self.chart_canvas.figure.autofmt_xdate()
        # Use a more precise date string for the x axis locations in the toolbar.
        self._static_ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
        self.chart_canvas.draw()

    def show_climate_engine_download(self):

        frm = FrmClimateEngineDownload(parent=self, qris_project=self.qris_project)
        frm.exec_()
        self.load_climate_engine_metrics()

    def export_data(self):
        
        # get the selected time series ids
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            QtWidgets.QMessageBox.warning(self, 'Export Climate Change Data', 'No time series selected')
            return
        # need to grab the data for each checked sample frame feature
        sample_frame_feature_ids = []
        for i in range(self.sample_frame_widget.sample_frames_model.rowCount(None)):
            index = self.sample_frame_widget.sample_frames_model.index(i)
            if self.sample_frame_widget.sample_frames_model.data(index, Qt.CheckStateRole) == Qt.Checked:
                sample_frame_feature_ids.append(self.sample_frame_widget.sample_frames_model.data(index, Qt.UserRole).id)

        if len(sample_frame_feature_ids) == 0:
            QtWidgets.QMessageBox.warning(self, 'Export Climate Change Data', 'No sample frame features selected')
            return
        time_series_id = time_series_ids[0].data(Qt.UserRole)

        # get the date range
        start_date, end_date = self.date_range_widget.get_date_range()

        # get the data for the selected time series
        data = {}

        
        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('SELECT * FROM time_series WHERE time_series_id = ?', (time_series_id,))
            time_series = curs.fetchone()
            time_series_name = time_series[1]
            dataset_id, variable_id = time_series_name.split(' ')
            dataset_name = next((key for key, dataset in self.datasets.items() if dataset['id'] == dataset_id), None)
            metadata = json.loads(time_series[5])
            y_label = metadata['units'] if 'units' in metadata else 'Value'
            for sample_frame_feature_id in sample_frame_feature_ids:
                curs.execute('SELECT time_value, value FROM sample_frame_time_series WHERE time_series_id = ? AND sample_frame_fid = ? AND time_value BETWEEN ? AND ?',
                             (time_series_id, sample_frame_feature_id, start_date, end_date))
                data[sample_frame_feature_id] = [(datetime.strptime(row[0], '%Y-%m-%d'), row[1]) for row in curs.fetchall()]

        # write the data to a CSV file
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Data', f'{dataset_name}_{variable_id}', 'CSV Files (*.csv)')[0]
        if file_name == '':
            return
        with open(file_name, 'w') as file:
            file.write('Date,')
            for sample_frame_feature_id in sample_frame_feature_ids:
                file.write(f'{sample_frame_feature_id},')
            file.write('\n')
            for i in range(len(data[sample_frame_feature_ids[0]])):
                file.write(f'{data[sample_frame_feature_ids[0]][i][0].strftime("%Y-%m-%d")},')
                for sample_frame_feature_id in sample_frame_feature_ids:
                    file.write(f'{data[sample_frame_feature_id][i][1]},')
                file.write('\n')

        # message box
        QtWidgets.QMessageBox.information(self, 'Export Climate Change Data', f'Data exported successfully to {file_name}')


    def setupUi(self):

        self.dockWidgetContents = QtWidgets.QWidget(self)
        self.setWidget(self.dockWidgetContents)

        self.horiz_main = QtWidgets.QHBoxLayout(self.dockWidgetContents)

        self.splitter = QtWidgets.QSplitter(self.dockWidgetContents)
        self.splitter.setSizes([300])
        self.horiz_main.addWidget(self.splitter)

        self.vert_left = QtWidgets.QVBoxLayout(self)

        self.widget_left = QtWidgets.QWidget(self)
        self.widget_left.setLayout(self.vert_left)
        self.splitter.addWidget(self.widget_left)

        self.tab_widget_left = QtWidgets.QTabWidget(self.widget_left)
        self.vert_left.addWidget(self.tab_widget_left)

        # Sample Frame Tab
        self.tab_sample_frame = QtWidgets.QWidget(self.widget_left)
        self.vert_sample_frame = QtWidgets.QVBoxLayout(self.tab_sample_frame)
        self.tab_sample_frame.setLayout(self.vert_sample_frame)
        self.tab_widget_left.addTab(self.tab_sample_frame, 'Sample Frame')

        self.vert_sample_frame.addWidget(self.sample_frame_widget)

        # Climate Engine Tab
        self.tab_climate_engine = QtWidgets.QWidget(self.widget_left)
        self.vert_climate_engine = QtWidgets.QVBoxLayout(self.tab_climate_engine)
        self.tab_climate_engine.setLayout(self.vert_climate_engine)
        self.tab_widget_left.addTab(self.tab_climate_engine, 'Climate Engine Metrics')

        self.horiz_climate_engine = QtWidgets.QHBoxLayout(self)
        self.vert_climate_engine.addLayout(self.horiz_climate_engine)

        self.btn_climate_engine = QtWidgets.QPushButton('Climate Engine')
        self.btn_climate_engine.setStyleSheet('QPushButton {text-decoration: underline; color: blue;}')
        self.btn_climate_engine.clicked.connect(open_climate_engine_website)
        self.horiz_climate_engine.addWidget(self.btn_climate_engine)

        # add a spacer between the buttons
        self.horiz_climate_engine.addStretch()

        self.btn_climate_engine_download = QtWidgets.QPushButton('Download Metrics')
        self.btn_climate_engine_download.clicked.connect(self.show_climate_engine_download)
        self.horiz_climate_engine.addWidget(self.btn_climate_engine_download)

        self.lst_climate_engine = QtWidgets.QListView(self.widget_left)
        self.lst_climate_engine.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lst_climate_engine.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.vert_climate_engine.addWidget(self.lst_climate_engine)

        # ok lets add the right side
        self.vert_right = QtWidgets.QVBoxLayout(self)
        self.widget_right = QtWidgets.QWidget(self)
        self.widget_right.setLayout(self.vert_right)
        self.splitter.addWidget(self.widget_right)

        self.horiz_right_top = QtWidgets.QHBoxLayout(self)
        self.vert_right.addLayout(self.horiz_right_top)

        self.horiz_right_top.addWidget(self.date_range_widget)

        self.lbl_chart_type = QtWidgets.QLabel('X-Axis Represents')
        font = self.lbl_chart_type.font()
        font.setBold(True)
        self.lbl_chart_type.setFont(font)
        self.horiz_right_top.addWidget(self.lbl_chart_type)

        self.rdo_time = QtWidgets.QRadioButton('Time')
        self.rdo_time.setChecked(True)
        self.horiz_right_top.addWidget(self.rdo_time)

        self.rdo_space = QtWidgets.QRadioButton('Space')
        self.rdo_space.setChecked(False)
        self.rdo_space.setEnabled(False)
        self.rdo_space.setToolTip('Not yet implemented')
        self.horiz_right_top.addWidget(self.rdo_space)

        self.rdo_time = QtWidgets.QRadioButton('Time')
        self.horiz_right_top.addWidget(self.rdo_time)
        
        self.horiz_right_top.addStretch()

        self.btn_export = QtWidgets.QPushButton('Export')
        self.btn_export.clicked.connect(self.export_data)
        self.horiz_right_top.addWidget(self.btn_export)

        self.btn_help = add_help_button(self, 'context/climate-engine-explorer')
        self.horiz_right_top.addWidget(self.btn_help)

        self.chart_canvas = FigureCanvas(Figure())
        self._static_ax = self.chart_canvas.figure.subplots()

        self.table_metadata = QtWidgets.QTableWidget(self)
        self.table_metadata.verticalHeader().hide()

        self.tab_widget_right = QtWidgets.QTabWidget(self)
        self.vert_right.addWidget(self.tab_widget_right)
        self.tab_widget_right.addTab(self.chart_canvas, 'Graphical')
        self.tab_widget_right.addTab(self.table_metadata, 'Metadata')
