import os
import sqlite3

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from PyQt5 import QtCore, QtGui, QtWidgets


class FrmAnalysisExplorer(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(FrmAnalysisExplorer, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle('Analysis Explorer')

    def browse_gpkg(self):

        # File dialog
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilter('GeoPackage (*.gpkg)')
        result = dlg.exec_()
        
        if result:
            if os.path.exists(dlg.selectedFiles()[0]):
                self.txtGPKG.setText(dlg.selectedFiles()[0])
                self.gpkg = dlg.selectedFiles()[0]
                self.load_geopackage()


    def load_geopackage(self):

        if self.gpkg is None:
            return
        
        self.widgetAnalysisExplorer.start_widget(self.gpkg)
            


    def setupUi(self, Dialog):

        self.vlayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.vlayout)
        
        self.grid = QtWidgets.QGridLayout()
        self.vlayout.addLayout(self.grid)

        self.lblGPKG = QtWidgets.QLabel('GeoPackage')
        self.grid.addWidget(self.lblGPKG, 0, 0)

        self.txtGPKG = QtWidgets.QLineEdit()
        self.txtGPKG.setReadOnly(True)
        self.grid.addWidget(self.txtGPKG, 0, 1)

        self.btnGPKG = QtWidgets.QPushButton('...')
        self.btnGPKG.clicked.connect(self.browse_gpkg)
        self.grid.addWidget(self.btnGPKG, 0, 2)

        self.widgetAnalysisExplorer = QWidgetAnalysisExplorer()
        self.vlayout.addWidget(self.widgetAnalysisExplorer)



class QWidgetAnalysisExplorer(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(QWidgetAnalysisExplorer, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Analysis Explorer')

        self.metrics = []
        self.sample_frame_features = []
        self.events = []

        self.cmbAnalysisType.addItems(['Metric over Time', 'Metric over Riverscape'])
        # Connect the currentIndexChanged signal to the on_analysis_type_changed method
        self.cmbAnalysisType.currentIndexChanged.connect(self.on_analysis_type_changed)

    def on_analysis_type_changed(self, index):
        # Call the appropriate method based on the selected index
        if index == 0:
            self.metric_over_time()
        elif index == 1:
            self.metric_over_riverscape()
        
    def start_widget(self, gpkg):

        self.gpkg = gpkg

        with sqlite3.connect(self.gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # get the analyses
            cursor.execute('SELECT * FROM analyses')
            self.analyses = cursor.fetchall()
            self.cmbAnalysis.addItems([a['name'] for a in self.analyses])
            self.cmbAnalysis.currentIndexChanged.connect(self.on_analysis_changed)

        self.cmbAnalysis.setEnabled(True)
        self.on_analysis_changed(0)
        self.metric_over_time()

    def on_analysis_changed(self, index):

        # ok lets get the metrics available for the selected analysis and load them into the metric combo box
        analysis = self.analyses[index]

        with sqlite3.connect(self.gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('select * from analysis_metrics Inner Join metrics on metric_id = analysis_metrics.metric_id WHERE analysis_metrics.analysis_id = ? Group BY id', (analysis['id'],))
            self.metrics = cursor.fetchall()
            self.cmbMetric.addItems([m['name'] for m in self.metrics])

            cursor.execute('SELECT * FROM sample_frame_features WHERE sample_frame_id = ?', (analysis['mask_id'],))
            self.sample_frame_features = cursor.fetchall()
            self.cmbSampleFrameFeature.addItems([sf['display_label'] for sf in self.sample_frame_features])

            cursor.execute('SELECT * FROM events')
            self.events = cursor.fetchall()
            self.cmbEvent.addItems([e['name'] for e in self.events])

        # make the plot type combo box enabled
        self.cmbAnalysisType.setEnabled(True)

    def metric_over_time(self):
    
        self.cmbEvent.setEnabled(False)
        self.cmbSampleFrameFeature.setEnabled(True)
        self.cmbMetric.setEnabled(True)

        self.cmbSampleFrameFeature.currentIndexChanged.connect(self.on_sample_frame_feature_changed)
        self.cmbMetric.currentIndexChanged.connect(self.on_metric_changed)

        self.plot_metric_over_time(self.metrics[0]['id'])

    def on_sample_frame_feature_changed(self, index):
        
        metric_index = self.cmbMetric.currentIndex()
        self.plot_metric_over_time(self.metrics[metric_index]['id'])  

    def on_metric_changed(self, index):

        metric_index = self.cmbMetric.currentIndex()
        if self.cmbAnalysisType.currentIndex() == 0:
            self.plot_metric_over_time(self.metrics[metric_index]['id'])
        else:
            self.plot_metric_over_riverscape(self.metrics[metric_index]['id'])

    def on_event_changed(self, index):

        metric_index = self.cmbMetric.currentIndex()
        self.plot_metric_over_riverscape(self.metrics[metric_index]['id'])
    
    def metric_over_riverscape(self):

        self.cmbEvent.setEnabled(True)
        self.cmbSampleFrameFeature.setEnabled(False)
        self.cmbMetric.setEnabled(True)

        self.cmbEvent.currentIndexChanged.connect(self.on_event_changed)
        self.cmbMetric.currentIndexChanged.connect(self.on_metric_changed)

        self.plot_metric_over_riverscape(self.metrics[0]['id'])

    def get_metric_values(self, analysis_id, metric_id):

        with sqlite3.connect(self.gpkg) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM metric_values WHERE analysis_id = ? AND metric_id = ?', (analysis_id, metric_id))
            return cursor.fetchall()
        

    def get_event_dates(self):

        with sqlite3.connect(self.gpkg) as conn:
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

        analysis_id = self.analyses[self.cmbAnalysis.currentIndex()]['id']
        metric_name = self.metrics[self.cmbMetric.currentIndex()]['name']

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
                    x.append(date)
                    y.append(m['automated_value'] if m['is_manual'] == 0 else m['manual_value'])
            
        ax: plt = self.plot.figure.add_subplot(111)
        ax.bar(x, y)
        ax.set_ylabel(metric_name)
        ax.set_xlabel('Time')
        ax.set_title(f'{metric_name} Over Time')
        self.plot.draw()

    def plot_metric_over_riverscape(self, metric_id):

        analysis_id = self.analyses[self.cmbAnalysis.currentIndex()]['id']

        self.plot.figure.clear()
        metric_values = self.get_metric_values(analysis_id, metric_id)

        event_date = self.cmbEvent.currentText()
        event_id = None
        for e in self.events:
            if e['name'] == event_date:
                event_id = e['id']
                break
        x = []
        y = []
        x_label = []
        topology = []

        for sample_frame_id in self.sample_frame_features:
            for m in metric_values:
                if m['sample_frame_feature_id'] == sample_frame_id['fid']:
                    if m['event_id'] != event_id:
                        continue
                    x.append(sample_frame_id['fid'])
                    y.append(m['automated_value'] if m['is_manual'] == 0 else m['manual_value'])
                    x_label.append(sample_frame_id['display_label'] if sample_frame_id['display_label'] is not None else sample_frame_id['fid'])
                    topology.append(sample_frame_id['flows_into'])

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
        self.grid.addWidget(self.cmbAnalysisType, 1, 1)

        self.lblMetric = QtWidgets.QLabel('Metric')
        self.grid.addWidget(self.lblMetric, 2, 0)

        self.cmbMetric = QtWidgets.QComboBox()
        self.cmbMetric.setEnabled(False)
        self.grid.addWidget(self.cmbMetric, 2, 1)

        self.lblEvent = QtWidgets.QLabel('Event')
        self.grid.addWidget(self.lblEvent, 3, 0)

        self.cmbEvent = QtWidgets.QComboBox()
        self.cmbEvent.setEnabled(False)
        self.grid.addWidget(self.cmbEvent, 3, 1)

        self.lblSampleFrameFeature = QtWidgets.QLabel('Sample Frame Feature')
        self.grid.addWidget(self.lblSampleFrameFeature, 5, 0)

        self.cmbSampleFrameFeature = QtWidgets.QComboBox()
        self.cmbSampleFrameFeature.setEnabled(False)
        self.grid.addWidget(self.cmbSampleFrameFeature, 5, 1)

        self.plot = FigureCanvas(Figure(figsize=(5, 3)))
        self.vlayout.addWidget(self.plot)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = FrmAnalysisExplorer()
    w.show()
    sys.exit(app.exec_())
