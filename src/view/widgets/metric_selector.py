from qgis.PyQt import QtCore, QtGui, QtWidgets

from ...model.project import Project
from ...model.metric import Metric
from ...model.analysis_metric import AnalysisMetric
from ...model.analysis import Analysis

from ..frm_layer_metric_details import FrmLayerMetricDetails

class MetricSelector(QtWidgets.QWidget):

    def __init__(self, parent, project: Project, analysis: Analysis = None):
        super(MetricSelector, self).__init__(parent)
        
        self.qris_project = project
        self.analysis = analysis
        
        self.setupUi()
        self.load_metrics_table()

    def setupUi(self):
        
        self.vert_metrics = QtWidgets.QVBoxLayout(self)
        self.vert_metrics.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vert_metrics)

        self.metricsTable = QtWidgets.QTableWidget(0, 8)
        # self.metricsTable.resize(500, 500) # Let layout handle size
        self.metricsTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.metricsTable.resizeColumnsToContents() # Call this after population
        
        self.metricsTable.setHorizontalHeaderLabels(['Protocol', 'Group', 'Metric', 'Version', 'Status', 'Availability', 'Usage', None])
        header = self.metricsTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(7, 10)
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

    def load_metrics_table(self):
        metrics = list(self.qris_project.metrics.values())
        # we need to filter the metrics by only those that are in a layer
        
        protocol_map = {p.machine_code: p.name for p in self.qris_project.protocols.values()}

        self.metricsTable.setRowCount(len(metrics))

        for row in range(len(metrics)):
            metric: Metric = metrics[row]
            level_id = metric.default_level_id
            if self.analysis is not None:
                if metric.id in self.analysis.analysis_metrics:
                    level_id = self.analysis.analysis_metrics[metric.id].level_id

            # Protocol
            prot_display = protocol_map.get(metric.protocol_machine_code, metric.protocol_machine_code)
            prot_item = QtWidgets.QTableWidgetItem()
            prot_item.setText(prot_display)
            prot_item.setData(QtCore.Qt.UserRole, metric)
            prot_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 0, prot_item)

            # Group (Hierarchy)
            group_item = QtWidgets.QTableWidgetItem()
            hierarchy = getattr(metric, 'hierarchy', [])
            group_item.setText(" > ".join(hierarchy) if hierarchy else "")
            group_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 1, group_item)

            # Metric
            label_item = QtWidgets.QTableWidgetItem()
            label_item.setText(metric.name)
            self.metricsTable.setItem(row, 2, label_item)
            label_item.setFlags(QtCore.Qt.ItemIsEnabled)

            # Version
            ver_item = QtWidgets.QTableWidgetItem()
            ver_item.setText(str(metric.version) if metric.version else "")
            ver_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 3, ver_item)

            # Status
            status = getattr(metric, 'status', 'active')
            status_item = QtWidgets.QTableWidgetItem()
            status_item.setText(status)
            status_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 4, status_item)

            # Availability
            calc_status = metric.get_automation_availability(self.qris_project)
            calc_item = QtWidgets.QTableWidgetItem()
            calc_item.setText(calc_status)
            calc_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 5, calc_item)

            # Usage
            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            self.metricsTable.setCellWidget(row, 6, cboStatus)

            # Help
            cmdHelp = QtWidgets.QPushButton()
            cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
            cmdHelp.setToolTip('Metric Definition')
            cmdHelp.clicked.connect(lambda _, m=metric: FrmLayerMetricDetails(self, self.qris_project, metric=m).exec_())
            self.metricsTable.setCellWidget(row, 7, cmdHelp)
        
        self.metricsTable.resizeColumnsToContents()

    def toggle_all_metrics(self, level_id: str):
            
            for row in range(self.metricsTable.rowCount()):
                cboStatus: QtWidgets.QComboBox = self.metricsTable.cellWidget(row, 6)
                # find from text
                idx = cboStatus.findText(level_id)
                cboStatus.setCurrentIndex(idx)

    def get_selected_metrics(self):
        analysis_metrics = {}
        for row in range(self.metricsTable.rowCount()):
            metric = self.metricsTable.item(row, 0).data(QtCore.Qt.UserRole)
            cboStatus = self.metricsTable.cellWidget(row, 6)
            level_id = cboStatus.currentData(QtCore.Qt.UserRole)
            if level_id > 0:
                analysis_metrics[metric.id] = AnalysisMetric(metric, level_id)
        return analysis_metrics
