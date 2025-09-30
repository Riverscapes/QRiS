import os
import sqlite3

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from ..model.project import Project
from ..model.db_item import DBItemModel
from ..model.event import DCE_EVENT_TYPE_ID
from ..model.analysis import Analysis
from ..model.metric import Metric
from ..model.sample_frame import get_sample_frame_ids, get_sample_frame_sequence

class FrmAnalysisExplorer(QtWidgets.QDialog):

    def __init__(self, parent=None, qris_project: Project = None, analysis_id=None):
        super(FrmAnalysisExplorer, self).__init__(parent)

        self.qris_project = qris_project

        self.widgetAnalysisExplorer = QWidgetAnalysisExplorer(self, self.qris_project, analysis_id)

        self.setupUi(self)

        self.setWindowTitle('Analysis Explorer')


    def setupUi(self, Dialog):

        self.vlayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.vlayout)
        
        self.grid = QtWidgets.QGridLayout()
        self.vlayout.addLayout(self.grid)

        self.vlayout.addWidget(self.widgetAnalysisExplorer)



class QWidgetAnalysisExplorer(QtWidgets.QWidget):

    def __init__(self, parent=None, qris_project: Project = None, analysis_id=None):
        super(QWidgetAnalysisExplorer, self).__init__(parent)

        self.qris_project = qris_project
        self.setupUi()

        self.setWindowTitle('Analysis Explorer')

        self.cmbAnalysisType.addItems(['Metric over Time', 'Metric over Riverscape'])
        self.cmbAnalysisType.currentIndexChanged.connect(self.on_analysis_type_changed)
        self.cmbAnalysisType.setEnabled(True)

        self.cmbAnalysis.setModel(DBItemModel(self.qris_project.analyses))
        self.cmbAnalysis.currentIndexChanged.connect(self.on_analysis_changed)
        self.cmbAnalysis.setEnabled(True)

        index = 0
        if analysis_id is not None:
            # Find the index of the analysis with the given ID
            for i in range(self.cmbAnalysis.count()):
                if self.cmbAnalysis.itemData(i, Qt.UserRole).id == analysis_id:
                    self.cmbAnalysis.setCurrentIndex(i)
                    index = i
                    break
        
        self.on_analysis_changed(index)
        self.metric_over_time()

    def on_analysis_type_changed(self, index):
        # Call the appropriate method based on the selected index
        if index == 0:
            self.metric_over_time()
        elif index == 1:
            self.metric_over_riverscape()

    def on_analysis_changed(self, index):

        self.analysis: Analysis = self.cmbAnalysis.currentData(Qt.UserRole)

        self.cmbMetric.clear()
        analysis_metrics = {i: analysis_metric.metric for i, analysis_metric in self.analysis.analysis_metrics.items()}
        metrics = DBItemModel(analysis_metrics)
        self.cmbMetric.setModel(metrics)

        sample_frame_features = get_sample_frame_ids(self.qris_project.project_file, self.analysis.sample_frame.id)
        self.cmbSampleFrameFeature.setModel(DBItemModel(sample_frame_features))

        self.cmbEvent.clear()
        events = DBItemModel({event_id: event for event_id, event in self.qris_project.events.items() if event.event_type.id == DCE_EVENT_TYPE_ID})
        self.cmbEvent.setModel(events)

    def metric_over_time(self):
    
        self.cmbEvent.setEnabled(False)
        self.cmbSampleFrameFeature.setEnabled(True)
        self.cmbMetric.setEnabled(True)

        self.cmbSampleFrameFeature.currentIndexChanged.connect(self.on_sample_frame_feature_changed)
        self.cmbMetric.currentIndexChanged.connect(self.on_metric_changed)

        if self.cmbMetric.count() > 0:
            self.plot_metric_over_time(self.cmbMetric.currentData(Qt.UserRole).id)

    def on_sample_frame_feature_changed(self, index):
        
        metric = self.cmbMetric.currentData(Qt.UserRole)
        self.plot_metric_over_time(metric.id)  

    def on_metric_changed(self, index):

        metric: Metric = self.cmbMetric.currentData(Qt.UserRole)
        if self.cmbAnalysisType.currentIndex() == 0:
            self.plot_metric_over_time(metric.id)
        else:
            self.plot_metric_over_riverscape(metric.id)

    def on_event_changed(self, index):

        metric = self.cmbMetric.currentData(Qt.UserRole)
        self.plot_metric_over_riverscape(metric.id)
    
    def metric_over_riverscape(self):

        self.cmbEvent.setEnabled(True)
        self.cmbSampleFrameFeature.setEnabled(False)
        self.cmbMetric.setEnabled(True)

        self.cmbEvent.currentIndexChanged.connect(self.on_event_changed)
        self.cmbMetric.currentIndexChanged.connect(self.on_metric_changed)

        self.plot_metric_over_riverscape(self.cmbMetric.currentData(Qt.UserRole).id)

    def get_metric_values(self, analysis_id, metric_id):

        gpkg = self.qris_project.project_file
        with sqlite3.connect(gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM metric_values WHERE analysis_id = ? AND metric_id = ?', (analysis_id, metric_id))
            return cursor.fetchall()
        

    def reload_metrics(self):

        self.cmbMetric.clear()
        metrics = DBItemModel(self.qris_project.metrics)
        self.cmbMetric.setModel(metrics)

    def get_event_dates(self):

        gpkg = self.qris_project.project_file
        with sqlite3.connect(gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM events')
            events = cursor.fetchall()

            event_dates = {}
            for event in events:
                year = event['start_year'] if event['start_year'] is not None else ''
                month = event['start_month'] if event['start_month'] is not None else ''
                day = event['start_day'] if event['start_day'] is not None else ''
                date = '{}-{}-{}'.format(year, month, day)
                event_dates[event['id']] = date

        return event_dates

    def plot_metric_over_time(self, metric_id):

        analysis_id = self.cmbAnalysis.currentData(Qt.UserRole).id
        metric_name = self.cmbMetric.currentData(Qt.UserRole).name
        sample_frame_feature_id = self.cmbSampleFrameFeature.currentData(Qt.UserRole).id

        self.plot.figure.clear()
        metric_values = self.get_metric_values(analysis_id, metric_id)

        event_dates = self.get_event_dates()

        # This is a bar chart with time on the y axis and metric values on the x axis
        #y = [event_dates[m['event_id']] for m in metric_values]
        y = []
        x = []
        for event_id, date in event_dates.items():
            for m in metric_values:
                if m['event_id'] == event_id:
                    if m['sample_frame_feature_id'] == sample_frame_feature_id:
                        x.append(date)
                        y.append(m['automated_value'] if m['is_manual'] == 0 else m['manual_value'])
            
        ax: plt = self.plot.figure.add_subplot(111)
        ax.bar(x, y)
        ax.set_ylabel(metric_name)
        ax.set_xlabel('Time')
        ax.set_title(f'{metric_name} Over Time')
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right', fontsize='x-small')
        self.plot.draw()

    def plot_metric_over_riverscape(self, metric_id):

        analysis_id = self.cmbAnalysis.currentData(Qt.UserRole).id


        self.plot.figure.clear()
        metric_values = self.get_metric_values(analysis_id, metric_id)

        event_date = self.cmbEvent.currentText()
        event_id = self.cmbEvent.currentData(Qt.UserRole).id

        x = []
        y = []
        x_label = []
        topology = []

        sample_frame_features = get_sample_frame_sequence(self.qris_project.project_file, self.analysis.sample_frame.id)

        for sample_frame_feature in sample_frame_features:
            for m in metric_values:
                if m['sample_frame_feature_id'] == sample_frame_feature.id:
                    if m['event_id'] != event_id:
                        continue
                    x.append(sample_frame_feature.id)
                    y.append(m['automated_value'] if m['is_manual'] == 0 else m['manual_value'])
                    x_label.append(sample_frame_feature.name if sample_frame_feature.name is not None else sample_frame_feature.id)

        use_topology = True
        # Check if the topology is valid.
        # There should be exactly one None value in the topology list
        if topology.count(None) != 1:
            use_topology = False
        # The topology should be a list of integers
        if not all(isinstance(item, int) for item in topology if item is not None):
            use_topology = False
        # There should be no duplicate values in the topology list
        if len(set(topology)) != len(topology):
            use_topology = False
        # all of the values in the topology list should be in the x list
        if not all(item in x for item in topology if item is not None):
            use_topology = False

        if use_topology: 
            # Create a dictionary mapping x to the next x (topology)
            topology_dict = {x: topo for x, topo in zip(x, topology)}

            # Find the first feature (which is not in the values of the dictionary)
            first_feature = next(x for x in x if x not in topology_dict.values())

            # Lists to hold the ordered x_label and y values
            ordered_x_label = []
            ordered_y = []

            # Start from the first feature and follow the links
            current_feature = first_feature
            while current_feature is not None:
                # Append the current feature's x_label and y to the ordered lists
                ordered_x_label.append(x_label[x.index(current_feature)])
                ordered_y.append(y[x.index(current_feature)])

                # Move to the next feature
                current_feature = topology_dict.get(current_feature)
        else:
            ordered_x_label = x_label
            ordered_y = y

        ax: plt = self.plot.figure.add_subplot(111)
        ax.plot(ordered_y)
        ax.set_xlabel('Sample Frame Feature')
        ax.set_xticks(range(len(ordered_x_label)))
        ax.set_xticklabels(ordered_x_label, rotation=45, ha='right')
        ax.set_ylabel('Metric Value')
        ax.set_title(f'Metric Across Riverscape for {event_date}')
        self.plot.draw()

        return

    def setupUi(self):
        
        self.vlayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.vlayout)
        
        self.grid = QtWidgets.QGridLayout()
        self.vlayout.addLayout(self.grid)

        self.lblAnalysis = QtWidgets.QLabel('Analysis')
        self.grid.addWidget(self.lblAnalysis, 0, 0)

        self.cmbAnalysis = QtWidgets.QComboBox()
        self.cmbAnalysis.setEnabled(False)
        self.grid.addWidget(self.cmbAnalysis, 0, 1)

        self.lblAnalysisType = QtWidgets.QLabel('Analysis Type')
        self.grid.addWidget(self.lblAnalysisType, 1, 0)

        self.cmbAnalysisType = QtWidgets.QComboBox()
        self.cmbAnalysisType.setEnabled(False)
        self.cmbAnalysisType.setToolTip('Select the type of analysis to perform, either a sample frame metric over time or a metric across a riverscape')
        self.grid.addWidget(self.cmbAnalysisType, 1, 1)

        self.lblMetric = QtWidgets.QLabel('Metric')
        self.grid.addWidget(self.lblMetric, 2, 0)

        self.cmbMetric = QtWidgets.QComboBox()
        self.cmbMetric.setEnabled(False)
        self.cmbMetric.setToolTip('Select the metric to display')
        self.grid.addWidget(self.cmbMetric, 2, 1)

        self.lblEvent = QtWidgets.QLabel('Event')
        self.grid.addWidget(self.lblEvent, 3, 0)

        self.cmbEvent = QtWidgets.QComboBox()
        self.cmbEvent.setEnabled(False)
        self.cmbEvent.setToolTip('Select the Data Capture Event to display')
        self.grid.addWidget(self.cmbEvent, 3, 1)

        self.lblSampleFrameFeature = QtWidgets.QLabel('Sample Frame Feature')
        self.grid.addWidget(self.lblSampleFrameFeature, 5, 0)

        self.cmbSampleFrameFeature = QtWidgets.QComboBox()
        self.cmbSampleFrameFeature.setEnabled(False)
        self.cmbSampleFrameFeature.setToolTip('Select the sample frame feature to display')
        self.grid.addWidget(self.cmbSampleFrameFeature, 5, 1)

        self.plot = FigureCanvas(Figure())
        self.vlayout.addWidget(self.plot)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = FrmAnalysisExplorer()
    w.show()
    sys.exit(app.exec_())
