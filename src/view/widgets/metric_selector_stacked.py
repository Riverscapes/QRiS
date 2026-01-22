from typing import Dict
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
        self.is_tree_view = True
        
        # Initialize state
        self.current_metrics_state: Dict[int, int] = {}
        self.init_state()

        self.setupUi()
        self.load_current_view()

    def on_metric_status_changed(self, metric_id: int, index: int):
        self.current_metrics_state[metric_id] = index

    def init_state(self):
        metrics = list(self.qris_project.metrics.values())
        for metric in metrics:
            level_id = metric.default_level_id
            if self.analysis is not None:
                if metric.id in self.analysis.analysis_metrics:
                    level_id = self.analysis.analysis_metrics[metric.id].level_id
            self.current_metrics_state[metric.id] = level_id

    def setupUi(self):
        
        self.vert_metrics = QtWidgets.QVBoxLayout(self)
        self.vert_metrics.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vert_metrics)

        # Stacked Widget
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.vert_metrics.addWidget(self.stackedWidget)

        # --- Page 0: Tree View ---
        self.pageTree = QtWidgets.QWidget()
        self.vboxTree = QtWidgets.QVBoxLayout(self.pageTree)
        self.vboxTree.setContentsMargins(0, 0, 0, 0)
        
        self.metricsTree = QtWidgets.QTreeWidget()
        self.metricsTree.setHeaderLabels(['Metric', 'Version', 'Status', 'Availability', 'Usage', ''])
        header = self.metricsTree.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Fixed)
        header.resizeSection(5, 40)
        self.metricsTree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.vboxTree.addWidget(self.metricsTree)
        
        self.stackedWidget.addWidget(self.pageTree)

        # --- Page 1: Table View ---
        self.pageTable = QtWidgets.QWidget()
        self.vboxTable = QtWidgets.QVBoxLayout(self.pageTable)
        self.vboxTable.setContentsMargins(0, 0, 0, 0)

        self.metricsTable = QtWidgets.QTableWidget(0, 8)
        self.metricsTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
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
        self.vboxTable.addWidget(self.metricsTable)

        self.stackedWidget.addWidget(self.pageTable)

        # Bottom Buttons
        self.horiz_metric_buttons = QtWidgets.QHBoxLayout()
        self.vert_metrics.addLayout(self.horiz_metric_buttons)

        self.cmdToggleView = QtWidgets.QPushButton(self.get_toggle_text())
        self.cmdToggleView.clicked.connect(self.toggle_view)
        self.horiz_metric_buttons.addWidget(self.cmdToggleView)

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

        # Initial Stack View
        self.stackedWidget.setCurrentIndex(0 if self.is_tree_view else 1)

    def get_toggle_text(self):
        return "Switch to Table View" if self.is_tree_view else "Switch to Tree View"

    def toggle_view(self):
        # Toggle Mode
        self.is_tree_view = not self.is_tree_view
        
        # Update UI
        self.cmdToggleView.setText(self.get_toggle_text())
        self.stackedWidget.setCurrentIndex(0 if self.is_tree_view else 1)
        
        # Load new view
        self.load_current_view()

    def load_current_view(self):
        if self.is_tree_view:
            self.load_metrics_tree()
        else:
            self.load_metrics_table()

    def load_metrics_tree(self):
        metrics = list(self.qris_project.metrics.values())
        protocol_map = {p.machine_code: p.name for p in self.qris_project.protocols.values()}
        
        self.metricsTree.clear()
        
        def find_or_create_item(parent, text):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.text(0) == text:
                    return child
            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, text)
            item.setExpanded(True)
            return item

        for metric in metrics:
            level_id = self.current_metrics_state.get(metric.id, 0)

            # 1. Protocol Node
            prot_display = protocol_map.get(metric.protocol_machine_code, metric.protocol_machine_code)
            prot_item = find_or_create_item(self.metricsTree.invisibleRootItem(), prot_display)

            # 2. Group Nodes
            current_parent = prot_item
            hierarchy = getattr(metric, 'hierarchy', [])
            if hierarchy:
                for group_name in hierarchy:
                    current_parent = find_or_create_item(current_parent, group_name)

            # 3. Metric Leaf
            metric_item = QtWidgets.QTreeWidgetItem(current_parent)
            metric_item.setText(0, metric.name)
            metric_item.setData(0, QtCore.Qt.UserRole, metric)
            
            # Version
            metric_item.setText(1, str(metric.version) if metric.version else "")

            # Status
            status = getattr(metric, 'status', 'active')
            metric_item.setText(2, status)

            # Availability
            calc_status = metric.get_automation_availability(self.qris_project)
            metric_item.setText(3, calc_status)

            # Usage
            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            cboStatus.setProperty("metric_item", metric_item) 
            cboStatus.currentIndexChanged.connect(lambda idx, m_id=metric.id: self.on_metric_status_changed(m_id, idx))
            self.metricsTree.setItemWidget(metric_item, 4, cboStatus)

            # Help
            cmdHelp = QtWidgets.QPushButton()
            cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
            cmdHelp.setToolTip('Metric Definition')
            cmdHelp.clicked.connect(lambda _, m=metric: FrmLayerMetricDetails(self, self.qris_project, metric=m).exec_())
            cmdHelp.setFixedWidth(30)
            self.metricsTree.setItemWidget(metric_item, 5, cmdHelp)

    def load_metrics_table(self):
        metrics = list(self.qris_project.metrics.values())
        protocol_map = {p.machine_code: p.name for p in self.qris_project.protocols.values()}

        self.metricsTable.setRowCount(len(metrics))

        for row in range(len(metrics)):
            metric: Metric = metrics[row]
            level_id = self.current_metrics_state.get(metric.id, 0)

            # Protocol
            prot_display = protocol_map.get(metric.protocol_machine_code, metric.protocol_machine_code)
            prot_item = QtWidgets.QTableWidgetItem()
            prot_item.setText(prot_display)
            prot_item.setData(QtCore.Qt.UserRole, metric) # Storing metric here for retrieval
            prot_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 0, prot_item)

            # Group
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
            cboStatus.currentIndexChanged.connect(lambda idx, m_id=metric.id: self.on_metric_status_changed(m_id, idx))
            self.metricsTable.setCellWidget(row, 6, cboStatus)

            # Help
            cmdHelp = QtWidgets.QPushButton()
            cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
            cmdHelp.setToolTip('Metric Definition')
            cmdHelp.clicked.connect(lambda _, m=metric: FrmLayerMetricDetails(self, self.qris_project, metric=m).exec_())
            self.metricsTable.setCellWidget(row, 7, cmdHelp)
        
        self.metricsTable.resizeColumnsToContents()

    def toggle_all_metrics(self, level_id_text: str):
        target_idx = 0
        if level_id_text == 'Metric': target_idx = 1
        elif level_id_text == 'Indicator': target_idx = 2
        
        for m_id in self.current_metrics_state:
            self.current_metrics_state[m_id] = target_idx
            
        self.load_current_view()

    def get_selected_metrics(self):
        analysis_metrics = {}
        # Iterate through project metrics or cache? 
        # Using cache is safer because it reflects the user's latest actions on the UI
        
        for metric_id, level_idx in self.current_metrics_state.items():
            if level_idx > 0:
                 # Need Metric object.
                 metric = self.qris_project.metrics.get(metric_id)
                 if metric:
                     # AnalysisMetric expects level_id as integer? 
                     # Yes, init(metric, level_id).
                     # Note: In cboStatus we used addItem('Name', value). 
                     # But here we stored currentIndex which aligns with 0, 1, 2. 
                     # Assuming logic holds: 0=None, 1=Metric, 2=Indicator.
                     # In previous code: addItem('None', 0)...
                     
                     analysis_metrics[metric_id] = AnalysisMetric(metric, level_idx)
        return analysis_metrics