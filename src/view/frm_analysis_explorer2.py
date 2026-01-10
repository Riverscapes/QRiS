import os
import sqlite3

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from ..model.project import Project
from ..model.db_item import DBItemModel, DBItem
from ..model.event import DCE_EVENT_TYPE_ID
from ..model.analysis import Analysis
from ..model.metric import Metric
from ..model.sample_frame import get_sample_frame_ids, get_sample_frame_sequence


class FrmAnalysisExplorer(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, analysis_id: int):
        super(FrmAnalysisExplorer, self).__init__(parent)

        self.qris_project = qris_project
        self.analysis_id = analysis_id
        self.analysis: Analysis = qris_project.analyses[analysis_id]

        # gpkg = self.qris_project.project_file
        # with sqlite3.connect(gpkg) as conn:
        #     conn.row_factory = sqlite3.Row
        #     cursor = conn.cursor()

        #     self.analysis = Analysis.load_analyses(cursor, analysis_id)
        #     cursor.execute('SELECT name FROM analyses WHERE id = ?', (self.analysis_id,))
        #     analysis_row = cursor.fetchone()
        #     self.analysis_title = analysis_row['name']

        self.setWindowTitle(f'{self.analysis.name} - Analysis Summary')
        self.setupUi()

        analysis_metrics = {i: analysis_metric.metric for i, analysis_metric in self.analysis.analysis_metrics.items()}
        metrics = DBItemModel(analysis_metrics)
        self.cmbMetric.setModel(metrics)

        self.cmbMetric.setFocus()

    def on_metric_changed(self, index):

        metric: DBItem = self.cmbMetric.currentData(Qt.UserRole)
        print(f'Metric changed to: {metric.name} (ID: {metric.id})')

        gpkg = self.qris_project.project_file

        metric_values_over_time = {}
        metric_values_over_space = {}
        with sqlite3.connect(gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM metric_values WHERE analysis_id = ? AND metric_id = ?', (self.analysis_id, metric.id))
            for row in cursor.fetchall():
                event_id = row['event_id']
                sample_frame_id = row['sample_frame_feature_id']
                metric_value = row['automated_value'] if row['is_manual'] == 0 else row['manual_value']

                if event_id not in metric_values_over_time:
                    metric_values_over_time[event_id] = []
                metric_values_over_time[event_id].append(metric_value)

                if sample_frame_id not in metric_values_over_space:
                    metric_values_over_space[sample_frame_id] = []
                metric_values_over_space[sample_frame_id].append(metric_value)

        self.metric_over_time_plot.figure.clear()
        ax: plt = self.metric_over_time_plot.figure.add_subplot(111)
        metric_over_time_plot_data = [values for event_id, values in metric_values_over_time.items()]
        bp = ax.boxplot(metric_over_time_plot_data, patch_artist=True)
        self.configure_chart(ax, 'Data Capture Events')
        self.configure_data_series(bp)

        self.metric_over_riverscape_plot.figure.clear()
        ax2: plt = self.metric_over_riverscape_plot.figure.add_subplot(111)
        metric_over_space_plot_data = [values for sfid, values in metric_values_over_space.items()]
        bp2 = ax2.boxplot(metric_over_space_plot_data, patch_artist=True)
        self.configure_chart(ax2, 'Riverscapes')
        self.configure_data_series(bp2)

        self.metric_over_time_plot.draw()
        self.metric_over_riverscape_plot.draw()

    def configure_chart(self, ax: plt, x_axis_label: str) -> None:

        ax.set_xlabel(x_axis_label)
        ax.set_ylabel(self.cmbMetric.currentText())
        ax.grid(True, which='major', color='lightgray', linestyle='-')
        ax.grid(True, which='minor', color='lightgray', linestyle='--')

        # Put the grid behind the plot elements
        ax.set_axisbelow(True)

    def configure_data_series(self, bp) -> None:

        # Change the fill color
        # bp['boxes'] is a list of the box objects
        for box in bp['boxes']:
            box.set_facecolor('skyblue')    # Interior color
            box.set_edgecolor('navy')       # Border color
            box.set_linewidth(2)            # Border thickness

    def setupUi(self):

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.cmbMetric = QtWidgets.QComboBox()
        self.cmbMetric.setToolTip('Select the metric to display')
        self.cmbMetric.currentIndexChanged.connect(self.on_metric_changed)
        form_layout.addRow('Metric', self.cmbMetric)

        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        self.metric_over_time_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.metric_over_time_tab, 'Metric Over Time')
        metric_over_time_layout = QtWidgets.QVBoxLayout()
        self.metric_over_time_tab.setLayout(metric_over_time_layout)

        cmd_save_metric_over_time = QtWidgets.QPushButton()
        cmd_save_metric_over_time.setIcon(QtGui.QIcon(QtGui.QIcon(':/plugins/qris_toolbar/save')))
        metric_over_time_layout.addWidget(cmd_save_metric_over_time)

        self.metric_over_time_plot = FigureCanvas(Figure())
        metric_over_time_layout.addWidget(self.metric_over_time_plot)

        self.metric_over_riverscape_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.metric_over_riverscape_tab, 'Metric Over Riverscape')
        metric_over_riverscape_layout = QtWidgets.QVBoxLayout()
        self.metric_over_riverscape_tab.setLayout(metric_over_riverscape_layout)

        self.metric_over_riverscape_plot = FigureCanvas(Figure())
        metric_over_riverscape_layout.addWidget(self.metric_over_riverscape_plot)
