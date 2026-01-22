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
        self.load_metrics_tree()

    def setupUi(self):
        
        self.vert_metrics = QtWidgets.QVBoxLayout(self)
        self.vert_metrics.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vert_metrics)

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
        self.vert_metrics.addWidget(self.metricsTree)

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

    def load_metrics_tree(self):
        metrics = list(self.qris_project.metrics.values())
        protocol_map = {p.machine_code: p.name for p in self.qris_project.protocols.values()}
        
        self.metricsTree.clear()
        
        # Helper to find or create tree item
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
            level_id = metric.default_level_id
            if self.analysis is not None:
                if metric.id in self.analysis.analysis_metrics:
                    level_id = self.analysis.analysis_metrics[metric.id].level_id

            # 1. Protocol Node
            prot_display = protocol_map.get(metric.protocol_machine_code, metric.protocol_machine_code)
            prot_item = find_or_create_item(self.metricsTree.invisibleRootItem(), prot_display)

            # 2. Group (Hierarchy) Nodes
            current_parent = prot_item
            hierarchy = getattr(metric, 'hierarchy', [])
            if hierarchy:
                for group_name in hierarchy:
                    current_parent = find_or_create_item(current_parent, group_name)

            # 3. Metric Leaf Node
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

            # Status ComboBox
            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            # Store reference to metric in combobox for easy retrieval if needed, 
            # though iterating the tree is usually better
            cboStatus.setProperty("metric_item", metric_item) 
            self.metricsTree.setItemWidget(metric_item, 4, cboStatus)

            # Help Button
            cmdHelp = QtWidgets.QPushButton()
            cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
            cmdHelp.setToolTip('Metric Definition')
            cmdHelp.clicked.connect(lambda _, m=metric: FrmLayerMetricDetails(self, self.qris_project, metric=m).exec_())
            cmdHelp.setFixedWidth(30)
            self.metricsTree.setItemWidget(metric_item, 5, cmdHelp)

    def toggle_all_metrics(self, level_id: str):
        iterator = QtWidgets.QTreeWidgetItemIterator(self.metricsTree)
        while iterator.value():
            item = iterator.value()
            cboStatus = self.metricsTree.itemWidget(item, 4)
            if isinstance(cboStatus, QtWidgets.QComboBox):
                idx = cboStatus.findText(level_id)
                cboStatus.setCurrentIndex(idx)
            iterator += 1

    def get_selected_metrics(self):
        analysis_metrics = {}
        iterator = QtWidgets.QTreeWidgetItemIterator(self.metricsTree)
        while iterator.value():
            item = iterator.value()
            metric = item.data(0, QtCore.Qt.UserRole)
            if metric: # Only leaf nodes have metric data
                cboStatus = self.metricsTree.itemWidget(item, 4)
                if isinstance(cboStatus, QtWidgets.QComboBox):
                    level_id = cboStatus.currentData(QtCore.Qt.UserRole)
                    # Note: QComboBox.currentData roles: default is UserRole. 
                    # check how we added items: addItem(text, userData).
                    # default role for addItem user data is UserRole.
                    # let's verify how we usually retrieve it. addItem('None', 0).
                    # cboStatus.currentData() should return 0, 1, 2.
                    
                    # Correction: cboStatus.currentData() returns the data for UserRole.
                    level_id = cboStatus.currentData() 
                    
                    if level_id is not None and level_id > 0:
                        analysis_metrics[metric.id] = AnalysisMetric(metric, level_id)
            iterator += 1
        return analysis_metrics
