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
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize

from .frm_climate_engine_download import FrmClimateEngineDownload
from .utilities import add_help_button
from .widgets.sample_frames import SampleFrameWidget
from .widgets.date_range import DateRangeWidget
from .widgets.event_library import EventLibraryWidget

from ..model.project import Project
from ..model.db_item import dict_factory
from ..model.sample_frame import SampleFrame
from ..model.basin_characteristics_table_view import BasinCharsTableModel

from ..lib.climate_engine import get_datasets, open_climate_engine_website
from ..QRiS.qris_map_manager import QRisMapManager

class FrmClimateEngineExplorer(QtWidgets.QDockWidget):

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, qris_map_manager: QRisMapManager):

        super().__init__(parent)

        self.qris_project = qris_project
        self.qris_map_manager = qris_map_manager
        self.datasets = get_datasets()

        self.sample_frame_widget = SampleFrameWidget(self, self.qris_project, self.qris_map_manager, first_index_empty=True, sample_frame_types=[SampleFrame.AOI_SAMPLE_FRAME_TYPE, SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE, SampleFrame.SAMPLE_FRAME_TYPE])
        self.sample_frame_widget.cbo_sample_frame.currentIndexChanged.connect(self.load_climate_engine_metrics)
        self.sample_frame_widget.sample_frame_changed.connect(self.load_climate_engine_metrics)
        self.sample_frame_widget.sample_frame_changed.connect(self.create_plot)

        self.date_range_widget = DateRangeWidget(self)
        self.date_range_widget.date_range_changed.connect(self.create_plot)

        self.event_library = EventLibraryWidget(self, self.qris_project)
        self.event_library.event_checked.connect(self.create_plot)

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
        sample_frame_feature_ids = self.sample_frame_widget.get_selected_sample_frame_feature_ids()
        if len(sample_frame_feature_ids) == 0:
            return

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
            curs.execute(f'SELECT time_series_id, name, metadata FROM time_series WHERE time_series_id IN ({placeholders})', time_series_ids)
            time_series_rows = curs.fetchall()

        # load the time series names into the list view
        self.time_series_model = QStandardItemModel()
        for row in time_series_rows:
            # the name should be the display, the time series id should be the data
            # lets see if description is in the metadata, if so append it to the text name
            metadata = json.loads(row[2])
            name = f'{row[1]} ({metadata["description"]})' if metadata and 'description' in metadata else row[1]
            item = QStandardItem(name)
            item.setData(row[0], Qt.UserRole)
            self.time_series_model.appendRow(item)
        self.lst_climate_engine.setModel(self.time_series_model)
        self.lst_climate_engine.selectionModel().selectionChanged.connect(self.set_date_range)
        self.lst_climate_engine.selectionModel().selectionChanged.connect(self.create_plot)
        self.lst_climate_engine.selectionModel().selectionChanged.connect(self.load_metadata)
        self.lst_climate_engine.update()

    def create_plot(self):

        if self.lst_climate_engine.model() is None:
            return

        self._static_ax.clear()

        # get the selected time series ids
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            return
        time_series_id = time_series_ids[0].data(Qt.UserRole)

        self.tab_widget_right.setVisible(True)
        self.lbl_initial_text.setVisible(False)

        event_dates = [(event.date, event.name) for event in self.event_library.get_selected_events()]
        # add vertical lines for the events
        for event_date, event_name in event_dates:
            year, month, day = event_date.split('-')
            if year == 'None':
                continue
            if month == 'None':
                event_date = f'{year}-01-01'
            elif day == 'None':
                event_date = f'{year}-{month}-01'
            date = datetime.strptime(event_date, '%Y-%m-%d')
            self._static_ax.axvline(date, color='black', linestyle='--', linewidth=1)
            # Annotate the event label above the line if labels are enabled
            if self.chk_event_labels.isChecked():
                ylim = self._static_ax.get_ylim()
                y_pos = ylim[1]  # Top of the plot
                self._static_ax.annotate(
                    event_name,
                    xy=(date, y_pos),
                    xytext=(0, 5),
                    textcoords='offset points',
                    ha='right',
                    va='bottom',
                    fontsize=9,
                    rotation=90,
                    color='black',
                    fontweight='bold'
        )

        # get the date range
        start_date, end_date = self.date_range_widget.get_date_range()

        # get the data for the selected time series
        data = {}
        # need to grab the data for each checked sample frame feature
        sample_frame_feature_ids = self.sample_frame_widget.get_selected_sample_frame_feature_ids()
        frame = self.sample_frame_widget.selected_sample_frame()
        
        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('SELECT * FROM time_series WHERE time_series_id = ?', (time_series_id,))
            time_series = curs.fetchone()
            time_series_name = time_series[1]
            time_series_metadata = json.loads(time_series[5])
            dataset_name = time_series_metadata.get('dataset', None)
            variable_id = time_series_metadata.get('variable', None)
            units = time_series_metadata.get('units', None)
            for sample_frame_feature_id in sample_frame_feature_ids:
                curs.execute('SELECT time_value, value FROM sample_frame_time_series WHERE time_series_id = ? AND sample_frame_fid = ? AND time_value BETWEEN ? AND ?',
                             (time_series_id, sample_frame_feature_id, start_date, end_date))
                values = [(datetime.strptime(row[0], '%Y-%m-%d'), row[1]) for row in curs.fetchall()]
                curs.execute('SELECT display_label FROM sample_frame_features WHERE fid = ?', (sample_frame_feature_id,))
                display_label = curs.fetchone()[0]
                if display_label is None or display_label == '':
                    display_label = f'Feature {sample_frame_feature_id}'
                data[display_label] = values

        # check the data if there is only one plot point per sample frame
        if all(len(values) <= 1 for values in data.values()):
            marker = 'o'
            markersize = 10
        else:
            marker = 'None'
            markersize = 5

        # create the plot
        self._static_ax.set_xlabel('Time')
        description = time_series_metadata.get('description', variable_id)
        y_label = f'{description} ({units})' if units is not None else description
        self._static_ax.set_title(f'{dataset_name} ({description})')
        if self.rdo_space.isChecked():
            for sample_frame_feature_id, values in data.items():
                self._static_ax.plot([value[0] for value in values], [value[1] for value in values], label=sample_frame_feature_id)
            self._static_ax.legend(title='Sample Frame Feature')
        elif self.rdo_time.isChecked():
            for sample_frame_feature_id, values in data.items():
                self._static_ax.plot([value[0] for value in values], [value[1] for value in values], label=sample_frame_feature_id)
            self._static_ax.legend(title='Sample Frame Feature', frameon=False)
        self._static_ax.set_ylabel(y_label)

        # apply the marker
        for line in self._static_ax.lines:
            line.set_marker(marker)
            line.set_markersize(markersize)

        # Add gridlines
        self._static_ax.grid(True, which='both', color='lightgrey', linestyle='-', linewidth=0.5)

        # Add minor ticks to both axes
        self._static_ax.minorticks_on()
        self._static_ax.tick_params(which='both', width=1)
        self._static_ax.tick_params(which='major', length=7)
        self._static_ax.tick_params(which='minor', length=4, color='gray')

        self.chart_canvas.figure.autofmt_xdate()
        # Use a more precise date string for the x axis locations in the toolbar.
        self._static_ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
        self.chart_canvas.draw()

    def load_metadata(self):

        # get the selected time series ids
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            return
        time_series_id = time_series_ids[0].data(Qt.UserRole)

        fields = {
            'name': 'Name',
            'source': 'Source',
            'url': 'URL',
            'description': 'Description'
        }

        with sqlite3.connect(self.qris_project.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()
            curs.execute('SELECT {} FROM time_series where time_series_id = ?'.format(','.join(fields.keys())), (time_series_id,))
            row = curs.fetchone()
            metadata_values = [(val, row[key]) for key, val in fields.items()]
            # now grab and parse the metadata json
            curs.execute('SELECT metadata FROM time_series where time_series_id = ?', (time_series_id,))
            metadata = json.loads(curs.fetchone()['metadata'])
            metadata_values.extend([(key, metadata[key]) for key in metadata.keys()])
            self.metadata_model = BasinCharsTableModel(metadata_values, ['Name', 'Value'])
        self.table_metadata.setModel(self.metadata_model)

    def show_climate_engine_download(self):

        sample_frame_id = self.sample_frame_widget.cbo_sample_frame.currentData(Qt.UserRole).id
        sample_frame_features = self.sample_frame_widget.get_selected_sample_frame_feature_ids()

        frm = FrmClimateEngineDownload(parent=self, qris_project=self.qris_project, sample_frame_id=sample_frame_id, sample_frame_feature_fids=sample_frame_features)
        frm.exec_()
        self.load_climate_engine_metrics()

    def export_data(self):
        
        # get the selected time series ids
        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            QtWidgets.QMessageBox.warning(self, 'Export Climate Change Data', 'No time series selected')
            return
        # need to grab the data for each checked sample frame feature
        sample_frame_feature_ids = self.sample_frame_widget.get_selected_sample_frame_feature_ids()

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
            dataset_name = next((key for key, dataset in self.datasets.items() if dataset['datasetId'] == dataset_id), None)
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


    def delete_time_series(self):

        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(self, 'Delete Time Series', 'Are you sure you want to delete the selected time series?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        time_series_ids = self.lst_climate_engine.selectedIndexes()
        if time_series_ids is None or len(time_series_ids) == 0:
            return
        
        time_series_id = time_series_ids[0].data(Qt.UserRole)
        with sqlite3.connect(self.qris_project.project_file) as conn:
            try:
                curs = conn.cursor()
                curs.execute('DELETE FROM sample_frame_time_series WHERE time_series_id = ?', (time_series_id,))
                curs.execute('DELETE FROM time_series WHERE time_series_id = ?', (time_series_id,))
                conn.commit()
                QtWidgets.QMessageBox.information(self, 'Delete Time Series', 'Time series deleted successfully.')
            except Exception as e:
                conn.rollback()
                QtWidgets.QMessageBox.warning(self, 'Delete Time Series', f'Error deleting time series: {e}')
                return
            
        self.load_climate_engine_metrics()
        self.lst_climate_engine.setCurrentIndex(self.time_series_model.index(0, 0))
        self.create_plot()

    def on_context(self, event):
        index = self.lst_climate_engine.indexAt(event)
        if not index.isValid():
            return

        menu = QtWidgets.QMenu()
        delete_action = QtWidgets.QAction(QIcon(f':/plugins/qris_toolbar/delete'), 'Delete Time Series', self)
        delete_action.triggered.connect(self.delete_time_series)
        menu.addAction(delete_action)
        menu.exec_(QCursor.pos())

    def setupUi(self):

        self.dockWidgetContents = QtWidgets.QWidget(self)
        self.setWidget(self.dockWidgetContents)

        self.horiz_main = QtWidgets.QHBoxLayout(self.dockWidgetContents)

        self.splitter = QtWidgets.QSplitter(self.dockWidgetContents)
        self.splitter.setSizes([241])
        self.horiz_main.addWidget(self.splitter)

        self.vert_left = QtWidgets.QVBoxLayout(self)

        self.widget_left = QtWidgets.QWidget(self)
        self.widget_left.setLayout(self.vert_left)
        self.splitter.addWidget(self.widget_left)

        self.tab_widget_left = QtWidgets.QTabWidget(self.widget_left)
        size = QSize(241, 429)
        self.tab_widget_left.setMinimumSize(size)
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
        self.tab_widget_left.addTab(self.tab_climate_engine, 'Timeseries Data')

        self.horiz_climate_engine = QtWidgets.QHBoxLayout(self)
        self.vert_climate_engine.addLayout(self.horiz_climate_engine)

        # add a spacer between the buttons
        self.horiz_climate_engine.addStretch()

        self.btn_climate_engine_download = QtWidgets.QPushButton('Download Timeseries')
        self.btn_climate_engine_download.clicked.connect(self.show_climate_engine_download)
        self.horiz_climate_engine.addWidget(self.btn_climate_engine_download)

        self.lst_climate_engine = QtWidgets.QListView(self.widget_left)
        self.lst_climate_engine.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lst_climate_engine.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.lst_climate_engine.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_climate_engine.customContextMenuRequested.connect(self.on_context)
        self.vert_climate_engine.addWidget(self.lst_climate_engine)

       # Events Tab
        self.tab_events = QtWidgets.QWidget(self.widget_left)
        self.vert_events = QtWidgets.QVBoxLayout(self.tab_events)
        self.tab_events.setLayout(self.vert_events)
        self.tab_widget_left.addTab(self.tab_events, 'Events')
        self.vert_events.addWidget(self.event_library)

        self.chk_event_labels = QtWidgets.QCheckBox('Show Event Labels')
        self.chk_event_labels.setChecked(True) 
        self.chk_event_labels.setToolTip('Show event labels on the plot')
        self.chk_event_labels.toggled.connect(self.create_plot)
        self.vert_events.addWidget(self.chk_event_labels)

        # ok lets add the right side
        self.vert_right = QtWidgets.QVBoxLayout(self)
        self.widget_right = QtWidgets.QWidget(self)
        self.widget_right.setLayout(self.vert_right)
        self.splitter.addWidget(self.widget_right)

        self.horiz_chart_controls = QtWidgets.QHBoxLayout(self)

        qframe_x_axis = QtWidgets.QFrame(self)
        qframe_x_axis.setLayout(QtWidgets.QHBoxLayout())
        qframe_x_axis.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins
        qframe_x_axis.layout().setSpacing(0)  # Remove spacing
        qframe_x_axis.setObjectName("qframe_x_axis")
        qframe_x_axis.setStyleSheet('QFrame#qframe_x_axis {border: 1px solid gray; border-radius: 3px; padding: 5px;}')
        # qframe_x_axis.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.horiz_chart_controls.addWidget(qframe_x_axis)

        self.lbl_chart_type = QtWidgets.QLabel('X-Axis Represents')
        font = self.lbl_chart_type.font()
        font.setBold(True)
        self.lbl_chart_type.setFont(font)
        qframe_x_axis.layout().addWidget(self.lbl_chart_type)

        self.rdo_time = QtWidgets.QRadioButton('Time')
        self.rdo_time.setChecked(True)
        qframe_x_axis.layout().addWidget(self.rdo_time)

        self.rdo_space = QtWidgets.QRadioButton('Space')
        self.rdo_space.setChecked(False)
        self.rdo_space.setEnabled(False)
        self.rdo_space.setToolTip('Not yet implemented')
        qframe_x_axis.layout().addWidget(self.rdo_space)

        qframe_date_range = QtWidgets.QFrame(self)
        qframe_date_range.setLayout(QtWidgets.QHBoxLayout())
        qframe_date_range.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins
        # qframe_date_range.layout().setSpacing(0)
        qframe_date_range.setObjectName("qframe_date_range")
        qframe_date_range.setStyleSheet('QFrame#qframe_date_range {border: 1px solid gray; border-radius: 3px; padding: 5px;}')
        self.horiz_chart_controls.addWidget(qframe_date_range)

        self.lbl_date_range = QtWidgets.QLabel('Date Range')
        font = self.lbl_date_range.font()
        font.setBold(True)
        self.lbl_date_range.setFont(font)
        qframe_date_range.layout().addWidget(self.lbl_date_range)

        qframe_date_range.layout().addWidget(self.date_range_widget)

        self.btn_date_range = QtWidgets.QPushButton('Full Range')
        self.btn_date_range.clicked.connect(self.date_range_widget.set_dates_to_bounds)
        qframe_date_range.layout().addWidget(self.btn_date_range)
        
        self.horiz_chart_controls.addStretch()

        self.btn_export = QtWidgets.QPushButton('Export')
        self.btn_export.clicked.connect(self.export_data)
        self.horiz_chart_controls.addWidget(self.btn_export)

        self.btn_help = add_help_button(self, 'context/climate-engine-explorer')
        self.horiz_chart_controls.addWidget(self.btn_help)

        self.btn_about_climate_engine = QtWidgets.QPushButton('About Climate Engine')
        self.btn_about_climate_engine.setStyleSheet('QPushButton {text-decoration: underline; color: blue;}')
        self.btn_about_climate_engine.clicked.connect(open_climate_engine_website)
        self.horiz_chart_controls.addWidget(self.btn_about_climate_engine)

        self.lbl_initial_text = QtWidgets.QLabel('Select a Sample Frame and Climate Engine Metric Timeseries to view data')
        self.vert_right.addWidget(self.lbl_initial_text)
        self.lbl_initial_text.setAlignment(Qt.AlignCenter)

        self.chart_canvas = FigureCanvas(Figure())
        self._static_ax = self.chart_canvas.figure.subplots()

        self.table_metadata = QtWidgets.QTableView(self)
        self.table_metadata.verticalHeader().hide()

        self.tab_widget_right = QtWidgets.QTabWidget(self)
        self.vert_right.addWidget(self.tab_widget_right)
        
        chart_widget = QtWidgets.QWidget(self)
        chart_widget.setLayout(QtWidgets.QVBoxLayout())
        chart_widget.layout().addLayout(self.horiz_chart_controls)
        chart_widget.layout().addWidget(self.chart_canvas)
        self.tab_widget_right.addTab(chart_widget, 'Graphical')
        self.tab_widget_right.addTab(self.table_metadata, 'Metadata')
        self.tab_widget_right.setVisible(False)

        self.vert_right.addLayout(self.horiz_chart_controls)

        self.tab_widget_left.resize(size)

        # # Set the stretch factors to let the second widget fill the rest of the space
        self.splitter.setStretchFactor(0, 0)  # First widget (left) does not stretch
        self.splitter.setStretchFactor(1, 1)  # Second widget (right) stretches to fill the rest