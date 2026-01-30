from typing import Dict
from qgis.PyQt import QtCore, QtGui, QtWidgets

from ...model.project import Project
from ...model.metric import Metric
from ...model.analysis_metric import AnalysisMetric
from ...model.analysis import Analysis

from ..frm_layer_metric_details import FrmLayerMetricDetails
from ..frm_metric_availability_matrix import FrmMetricAvailabilityMatrix

class CheckableComboBox(QtWidgets.QComboBox):
    # Custom signal to notify when the popup is closed (edit finished)
    popupClosed = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.setModel(QtGui.QStandardItemModel(self))
        self.view().viewport().installEventFilter(self)
        self.model().dataChanged.connect(self.updateText)
        self.is_batch_mode = False # Flag to suppress updates
        self.all_checked_text = "All"
        self.none_checked_text = "None"
        self.empty_text = "No Options"

    def setPlaceholderText(self, text):
        super().setPlaceholderText(text)
        self.all_checked_text = text
        self.updateText()
        
    def setNoneCheckedText(self, text):
        self.none_checked_text = text
        self.updateText()
        
    def setEmptyText(self, text):
        self.empty_text = text
        self.updateText()

    def eventFilter(self, obj, event):
        if obj == self.view().viewport() and event.type() == QtCore.QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self.model().itemFromIndex(index)
                
                # Check for commands
                data = item.data()
                if data == "SELECT_ALL":
                    self.set_all_check_state(QtCore.Qt.Checked)
                elif data == "SELECT_NONE":
                    self.set_all_check_state(QtCore.Qt.Unchecked)
                elif item.isCheckable():
                    # Normal toggle
                    if item.checkState() == QtCore.Qt.Checked:
                        item.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        item.setCheckState(QtCore.Qt.Checked)
            return True # Consume event to prevent popup close
        return super(CheckableComboBox, self).eventFilter(obj, event)

    def set_all_check_state(self, state):
        self.is_batch_mode = True
        self.model().blockSignals(True)
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.isCheckable():
                item.setCheckState(state)
        self.model().blockSignals(False)
        self.is_batch_mode = False
        self.updateText() 
        
    def hidePopup(self):
        super(CheckableComboBox, self).hidePopup()
        self.popupClosed.emit()

    def addItem(self, text, data=None):
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole) # Default checked
        if data is not None:
             item.setData(data)
        self.model().appendRow(item)
        if not self.is_batch_mode:
            self.updateText()

    def addBatchItems(self, items):
        """Adds multiple items efficiently. items = list of (text, data) tuples."""
        self.is_batch_mode = True
        self.model().blockSignals(True)
        for text, data in items:
            self.addItem(text, data)
        self.model().blockSignals(False)
        self.is_batch_mode = False
        self.updateText()

    def add_command_item(self, text, data):
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        item.setData(data)
        font = item.font()
        font.setItalic(True)
        item.setFont(font)
        self.model().appendRow(item)

    def updateText(self, *args):
        items = self.get_checked_items()
        
        # Count checkable items only
        total_checkable = 0
        for i in range(self.model().rowCount()):
            if self.model().item(i).isCheckable():
                total_checkable += 1
                
        text = ", ".join(items)
        
        if total_checkable == 0:
            text = self.empty_text
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            if len(items) == total_checkable:
                text = self.all_checked_text
            elif len(items) == 0:
                text = self.none_checked_text
            elif len(items) > 3:
                text = f"{len(items)} selected"

        self.lineEdit().setText(text)
    
    def get_checked_items(self):
        checkedItems = []
        for i in range(self.count()):
            item = self.model().item(i)
            if item.checkState() == QtCore.Qt.Checked:
                checkedItems.append(item.text())
        return checkedItems
        
    def get_checked_data(self):
        checkedData = []
        for i in range(self.count()):
            item = self.model().item(i)
            if item.checkState() == QtCore.Qt.Checked:
                checkedData.append(item.data())
        return checkedData

class MetricSelector(QtWidgets.QWidget):

    def __init__(self, parent, project: Project, analysis: Analysis = None):
        super(MetricSelector, self).__init__(parent)
        
        self.qris_project = project
        self.analysis = analysis
        self.analysis_metadata = self.analysis.metadata.copy() if self.analysis and self.analysis.metadata else {}
        self.is_tree_view = True
        self.limit_dces = None
        
        # Initialize state
        self.current_metrics_state: Dict[int, int] = {}
        self.init_state()

        self.setupUi()
        self.load_filters()
        self.load_current_view()

    def apply_smart_filtering_for_existing_analysis(self):
        # 1. Limit to In Use Metrics
        self.act_limit_metrics.setChecked(True)
        
        # 2. Check if we need to expand the universe for experimental/deprecated metrics currently in use
        enable_experimental = False
        enable_deprecated = False
        
        for metric_id, level_id in self.current_metrics_state.items():
            if level_id > 0:
                metric = self.qris_project.metrics.get(metric_id)
                if not metric: continue
                
                # Check Deprecated
                if getattr(metric, 'status', 'active') == 'deprecated':
                    enable_deprecated = True
                
                # Check Experimental (via Protocol)
                protocol_machine_code = metric.protocol_machine_code
                # We need to find the protocol object to check its name/properties
                # Assuming I can look it up in qris_project.protocols
                # Finding by machine_code...
                protocol = None
                for p in self.qris_project.protocols.values():
                    if p.machine_code == protocol_machine_code:
                        protocol = p
                        break
                
                if protocol:
                     # Check if protocol status is experimental
                     # We might store status in metadata, or check name. 
                     # Ideally Protocol object has a status attribute or similar.
                     # Based on grep results, xml has status="experimental".
                     # The python object seems to not expose it explicitly as a property in __init__ 
                     # but likely passes it via metadata or we check name as fallback.
                     
                     # Check protocol metadata first (if available)
                     p_status = ""
                     if protocol.metadata and isinstance(protocol.metadata, dict):
                         p_status = protocol.metadata.get('status', "")
                         
                     # Fallback to name check if status not clearly experimental
                     if p_status.lower() == "experimental" or "experimental" in protocol.name.lower():
                         enable_experimental = True
                         
                     # Also check for experimental status attribute if it exists
                     if hasattr(protocol, 'status') and protocol.status == 'experimental':
                         enable_experimental = True

        if enable_experimental:
            self.act_include_experimental.setChecked(True)
        
        if enable_deprecated:
            self.act_include_deprecated.setChecked(True)

    def get_metric_font(self, metric, level_id):
        font = QtGui.QFont()
        status = getattr(metric, 'status', 'active')
        
        # Check if Protocol is Deprecated
        # lookup protocol by machine code
        protocol_status = 'active'
        if hasattr(self.qris_project, 'protocols'): # Safety check
            for p in self.qris_project.protocols.values():
                if p.machine_code == metric.protocol_machine_code:
                    if getattr(p, 'status', 'active') == 'deprecated':
                        protocol_status = 'deprecated'
                    break

        if level_id > 0:
            font.setBold(True)
            
        if status == 'deprecated' or protocol_status == 'deprecated':
            font.setItalic(True)
            if protocol_status == 'deprecated':
                 font.setStrikeOut(True) # Optional visual cue for protocol-level deprecation
            
        return font

    def on_metric_status_changed(self, metric_id: int, index: int):
        self.current_metrics_state[metric_id] = index
        
        # Get Font
        # We need the metric object to determine deprecated status, which we can get from the item traversal below 
        # provided we find it.
        
        # Update text for sorting in Tree
        iterator = QtWidgets.QTreeWidgetItemIterator(self.metricsTree)
        usage_display = ['None', 'Metric', 'Indicator'][index] if 0 <= index <= 2 else 'None'
        while iterator.value():
            item = iterator.value()
            metric = item.data(0, QtCore.Qt.UserRole)
            if metric and metric.id == metric_id:
                 item.setText(3, usage_display)
                 
                 # Update Font
                 font = self.get_metric_font(metric, index)
                 item.setFont(0, font)
                 item.setFont(1, font)
                 break
            iterator += 1
        
        # Update text for sorting in Table
        for row in range(self.metricsTable.rowCount()):
             item = self.metricsTable.item(row, 0)
             if not item: continue
             metric = item.data(QtCore.Qt.UserRole)
             if metric and metric.id == metric_id:
                 usage_item = self.metricsTable.item(row, 5)
                 if usage_item:
                     usage_item.setText(usage_display)
                 
                 # Update Font (Name and Version)
                 font = self.get_metric_font(metric, index)
                 if self.metricsTable.item(row, 2): self.metricsTable.item(row, 2).setFont(font)
                 if self.metricsTable.item(row, 3): self.metricsTable.item(row, 3).setFont(font)
                 break
        
        self.update_usage_count_label()
                 
    def init_state(self):
        metrics = list(self.qris_project.metrics.values())
        for metric in metrics:
            if self.analysis is not None:
                if metric.id in self.analysis.analysis_metrics:
                    level_id = self.analysis.analysis_metrics[metric.id].level_id
                else:
                    level_id = 0
            else:
                # New Analysis - Start clean
                level_id = 0
            self.current_metrics_state[metric.id] = level_id

    def setupUi(self):
        
        self.vert_metrics = QtWidgets.QVBoxLayout(self)
        self.vert_metrics.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vert_metrics)

        # Filters
        self.horiz_filters = QtWidgets.QHBoxLayout()
        self.vert_metrics.addLayout(self.horiz_filters)

        self.cbo_filter_protocol = CheckableComboBox()
        self.cbo_filter_protocol.setPlaceholderText("All Protocols")
        self.cbo_filter_protocol.setNoneCheckedText("No Protocols Selected")
        self.cbo_filter_protocol.setEmptyText("No Protocols Available")
        self.cbo_filter_protocol.popupClosed.connect(self.on_protocol_filter_changed)
        self.horiz_filters.addWidget(self.cbo_filter_protocol)
        
        self.cbo_filter_group = CheckableComboBox()
        self.cbo_filter_group.setPlaceholderText("All Groups")
        self.cbo_filter_group.setNoneCheckedText("No Groups Selected")
        self.cbo_filter_group.setEmptyText("No Groups Available")
        self.cbo_filter_group.popupClosed.connect(self.update_visibility)
        self.cbo_filter_group.setMinimumWidth(150)
        self.horiz_filters.addWidget(self.cbo_filter_group)
        
        self.txt_filter_search = QtWidgets.QLineEdit()
        self.txt_filter_search.setPlaceholderText("Search Metrics...")
        self.txt_filter_search.textChanged.connect(self.update_visibility)
        self.txt_filter_search.setMinimumWidth(200)
        self.horiz_filters.addWidget(self.txt_filter_search)

        self.btn_clear_filters = QtWidgets.QPushButton()
        self.btn_clear_filters.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/clear_filter'))
        self.btn_clear_filters.setToolTip("Clear Filters")
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        self.horiz_filters.addWidget(self.btn_clear_filters)

        self.lbl_filter_count = QtWidgets.QLabel("")
        self.horiz_filters.addWidget(self.lbl_filter_count)

        self.horiz_filters.addStretch()

        self.btn_advanced = QtWidgets.QToolButton()
        self.btn_advanced.setText("Advanced Filters")
        self.btn_advanced.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btn_advanced.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        
        self.menu_advanced = QtWidgets.QMenu(self.btn_advanced)
        
        self.act_limit_metrics = self.menu_advanced.addAction("Limit to Currently In Use Metrics")
        self.act_limit_metrics.setCheckable(True)
        self.act_limit_metrics.toggled.connect(self.update_visibility)
        
        self.menu_advanced.addSeparator()

        # Type Filters Group
        self.type_filter_group = QtWidgets.QActionGroup(self)
        self.type_filter_group.setExclusive(True)

        self.act_show_all = self.menu_advanced.addAction("Show All Metric Types")
        self.act_show_all.setCheckable(True)
        self.act_show_all.setChecked(True) # Default
        self.act_show_all.toggled.connect(self.update_visibility)
        self.type_filter_group.addAction(self.act_show_all)

        self.act_limit_feasible = self.menu_advanced.addAction("Automated: Ready for Calculation")
        self.act_limit_feasible.setCheckable(True)
        self.act_limit_feasible.setToolTip("Show only metrics that can be calculated automatically for at least one DCE.")
        self.act_limit_feasible.toggled.connect(self.update_visibility)
        self.type_filter_group.addAction(self.act_limit_feasible)

        self.act_limit_blocked = self.menu_advanced.addAction("Automated: Setup Required (Events/Inputs)")
        self.act_limit_blocked.setCheckable(True)
        self.act_limit_blocked.setToolTip("Show metrics that support automation but are missing required inputs or layers.")
        self.act_limit_blocked.toggled.connect(self.update_visibility)
        self.type_filter_group.addAction(self.act_limit_blocked)

        self.act_limit_manual = self.menu_advanced.addAction("Manual Entry Only")
        self.act_limit_manual.setCheckable(True)
        self.act_limit_manual.toggled.connect(self.update_visibility)
        self.type_filter_group.addAction(self.act_limit_manual)
        
        self.menu_advanced.addSeparator()
        
        self.act_include_experimental = self.menu_advanced.addAction("Include Experimental Protocols")
        self.act_include_experimental.setCheckable(True)
        self.act_include_experimental.toggled.connect(self.on_universe_changed)
        
        self.act_include_deprecated = self.menu_advanced.addAction("Include Deprecated Metrics")
        self.act_include_deprecated.setCheckable(True)
        self.act_include_deprecated.toggled.connect(self.on_universe_changed)
        
        self.btn_advanced.setMenu(self.menu_advanced)

        self.horiz_filters.addWidget(self.btn_advanced)

        # Stacked Widget
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.vert_metrics.addWidget(self.stackedWidget)

        # --- Page 0: Tree View ---
        self.pageTree = QtWidgets.QWidget()
        self.vboxTree = QtWidgets.QVBoxLayout(self.pageTree)
        self.vboxTree.setContentsMargins(0, 0, 0, 0)
        
        self.metricsTree = QtWidgets.QTreeWidget()
        self.metricsTree.setHeaderLabels(['Metric', 'Version (Status)', 'Availability', 'Usage', 'Description'])
        
        # Header Tooltips
        headerItem = self.metricsTree.headerItem()
        headerItem.setToolTip(0, "Name of the metric or indicator.")
        headerItem.setToolTip(1, "Version number and active status.")
        headerItem.setToolTip(2, "Summary of the ability to calculatete metrics automatically based on the current layers and inputs for each DCE in the Project.")
        headerItem.setToolTip(3, "Select usage level: Metric or Indicator. These will be included in the analysis accordingly.")
        headerItem.setToolTip(4, "Description of the metric.")

        header = self.metricsTree.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Interactive)
        self.metricsTree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.metricsTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.metricsTree.customContextMenuRequested.connect(self.open_tree_context_menu)
        self.metricsTree.setSortingEnabled(True)
        self.vboxTree.addWidget(self.metricsTree)
        
        self.stackedWidget.addWidget(self.pageTree)

        # --- Page 1: Table View ---
        self.pageTable = QtWidgets.QWidget()
        self.vboxTable = QtWidgets.QVBoxLayout(self.pageTable)
        self.vboxTable.setContentsMargins(0, 0, 0, 0)

        self.metricsTable = QtWidgets.QTableWidget(0, 7)
        self.metricsTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.metricsTable.setHorizontalHeaderLabels(['Protocol', 'Group', 'Metric', 'Version (Status)', 'Availability', 'Usage', 'Description'])
        
        # Header Tooltips
        table_tooltips = [
            "The protocol that defines this metric.",
            "Hierarchical group/category.",
            "Name of the metric or indicator.",
            "Version number and active status.",
            "Automation availability status based on current inputs.",
            "Select usage level: Metric or Indicator.",
            "Description of the metric."
        ]
        for i, tip in enumerate(table_tooltips):
            if self.metricsTable.horizontalHeaderItem(i):
                self.metricsTable.horizontalHeaderItem(i).setToolTip(tip)

        header = self.metricsTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.Interactive)
        self.metricsTable.verticalHeader().setVisible(False)
        self.metricsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.metricsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.metricsTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.metricsTable.customContextMenuRequested.connect(self.open_table_context_menu)
        self.metricsTable.setSortingEnabled(True)
        self.vboxTable.addWidget(self.metricsTable)

        self.stackedWidget.addWidget(self.pageTable)

        # Bottom Buttons
        self.horiz_metric_buttons = QtWidgets.QHBoxLayout()
        self.vert_metrics.addLayout(self.horiz_metric_buttons)

        self.cmdToggleView = QtWidgets.QPushButton(self.get_toggle_text())
        self.cmdToggleView.clicked.connect(self.toggle_view)
        self.horiz_metric_buttons.addWidget(self.cmdToggleView)

        self.lbl_usage_count = QtWidgets.QLabel("")
        self.horiz_metric_buttons.addWidget(self.lbl_usage_count)

        self.horiz_metric_buttons.addStretch()

        self.lbl_metric_set_all = QtWidgets.QLabel('Set Currently Displayed Metrics to:')
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

        self.cmd_set_defaults = QtWidgets.QPushButton('Default Usage')
        font = self.cmd_set_defaults.font()
        font.setBold(True)
        self.cmd_set_defaults.setFont(font)
        self.cmd_set_defaults.clicked.connect(lambda: self.toggle_all_metrics('Default'))
        self.horiz_metric_buttons.addWidget(self.cmd_set_defaults)

        # Build views once
        self.build_metrics_tree()
        self.build_metrics_table()
        
        # Apply Logic from User Settings (Must be after views are built because toggling triggers update_visibility)
        settings = QtCore.QSettings('Riverscapes', 'QRiS')
        show_experimental = settings.value('show_experimental_protocols', False, bool)
        
        if show_experimental:
            self.act_include_experimental.setChecked(True)

        # Apply intelligent filtering if loading an existing analysis
        if self.analysis is not None:
             self.apply_smart_filtering_for_existing_analysis()

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

    def set_analysis_metadata(self, metadata: dict):
        self.analysis_metadata = metadata
        self.refresh_availability()
        self.update_visibility()

    def set_selected_dces(self, dce_ids: list):
        self.limit_dces = dce_ids
        self.refresh_availability()
        self.update_visibility()

    def refresh_availability(self):
        # Update Tree
        it = QtWidgets.QTreeWidgetItemIterator(self.metricsTree)
        while it.value():
            item = it.value()
            metric = item.data(0, QtCore.Qt.UserRole)
            if metric:
                 status = metric.get_automation_availability(self.qris_project, self.analysis_metadata, self.limit_dces)
                 item.setText(2, status)
            it += 1
        
        # Update Table
        self.metricsTable.setSortingEnabled(False)
        for row in range(self.metricsTable.rowCount()):
             metric_item = self.metricsTable.item(row, 0)
             if metric_item:
                 metric = metric_item.data(QtCore.Qt.UserRole)
                 if metric:
                     status = metric.get_automation_availability(self.qris_project, self.analysis_metadata, self.limit_dces)
                     # Column 4 is Availability
                     avail_item = self.metricsTable.item(row, 4)
                     if avail_item:
                         avail_item.setText(status)
        self.metricsTable.setSortingEnabled(True)

    def on_protocol_filter_changed(self):
        self.update_group_filter()
        self.update_visibility()

    def on_universe_changed(self):
        self.load_filters()
        self.update_visibility()

    def load_filters(self):
        # Gather unique protocols
        protocols = set()
        
        for metric in self.qris_project.metrics.values():
            if self.is_metric_in_universe(metric):
                protocols.add(metric.protocol_machine_code)
            
        # Populate Protocol Filter
        self.cbo_filter_protocol.clear()
        
        # Map protocol codes to names if possible
        protocol_map = {p.machine_code: p.name for p in self.qris_project.protocols.values()}
        
        sorted_protocols = sorted(list(protocols))
        
        if sorted_protocols:
            self.cbo_filter_protocol.add_command_item("(Select All)", "SELECT_ALL")
            self.cbo_filter_protocol.add_command_item("(Select None)", "SELECT_NONE")
            self.cbo_filter_protocol.insertSeparator(self.cbo_filter_protocol.count())

        items_to_add = []
        for p_code in sorted_protocols:
            p_name = protocol_map.get(p_code, p_code)
            items_to_add.append((p_name, p_code))
        
        self.cbo_filter_protocol.addBatchItems(items_to_add)
        
        # Initial Population of Group Filter
        self.update_group_filter()

    def update_group_filter(self):
        # Identify unchecked items to preserve their state
        unchecked_items = set()
        for i in range(self.cbo_filter_group.count()):
            item = self.cbo_filter_group.model().item(i)
            if item.isCheckable() and item.checkState() == QtCore.Qt.Unchecked:
                 unchecked_items.add(item.text())

        # Determine available groups based on selected protocols
        sel_protocols = self.cbo_filter_protocol.get_checked_data()
        
        available_groups = set()
        protocol_count = self.cbo_filter_protocol.count()
        # If no protocols in filter (empty project?), loop won't run.
        # If protocols exist, sel_protocols might be empty (Select None).
        
        for metric in self.qris_project.metrics.values():
            if not self.is_metric_in_universe(metric):
                continue
            
            # If we have protocol items, filter by them.
            if protocol_count > 0:
                if metric.protocol_machine_code not in sel_protocols:
                    continue
            
            if hasattr(metric, 'hierarchy') and metric.hierarchy:
                for group in metric.hierarchy:
                    available_groups.add(group)

        # Repopulate Group Filter
        self.cbo_filter_group.clear()
        sorted_groups = sorted(list(available_groups))
        
        if sorted_groups:
            self.cbo_filter_group.add_command_item("(Select All)", "SELECT_ALL")
            self.cbo_filter_group.add_command_item("(Select None)", "SELECT_NONE")
            self.cbo_filter_group.insertSeparator(self.cbo_filter_group.count())

        items_to_add = []
        for group in sorted_groups:
             items_to_add.append((group, group))
        
        self.cbo_filter_group.addBatchItems(items_to_add)

        # Restore unchecked state (after batch adds)
        # We need to find items and uncheck them.
        self.cbo_filter_group.model().blockSignals(True)
        for i in range(self.cbo_filter_group.count()):
            item = self.cbo_filter_group.model().item(i)
            if item.text() in unchecked_items:
                item.setCheckState(QtCore.Qt.Unchecked)
        self.cbo_filter_group.model().blockSignals(False)
        self.cbo_filter_group.updateText() # Update text after restoring selections
            
        # Force text update in case we unchecked items manually without signal
        self.cbo_filter_group.updateText()

    def should_show_metric(self, metric):
        sel_protocols = self.cbo_filter_protocol.get_checked_data()
        sel_groups = self.cbo_filter_group.get_checked_data()
        search_text = self.txt_filter_search.text().lower().strip()

        prot_count = self.cbo_filter_protocol.count()
        group_count = self.cbo_filter_group.count()
        
        # 1. Search Text Check
        if search_text:
            # Check name, protocol, hierarchy
            name_match = search_text in metric.name.lower()
            if not name_match:
                # Optionally check other fields if desired
                return False

        # 2. Advanced Filters
        if self.act_limit_metrics.isChecked():
            if self.current_metrics_state.get(metric.id, 0) == 0:
                return False
        
        # Availability Status Check
        status = metric.get_automation_availability(self.qris_project, self.analysis_metadata, self.limit_dces)
        status_lower = status.lower()
        is_manual = "manual" in status_lower

        if self.act_limit_feasible.isChecked():
            # Must contain "DCE" and NOT start with "No" to be considered "Ready"
            # (e.g. "All 5 DCEs", "1 DCE")
            if "dce" not in status_lower or status_lower.startswith("no"):
                return False

        if self.act_limit_blocked.isChecked():
            # Must start with "No DCEs" (implies Missing Inputs or Selected or just empty)
            # But must NOT be manual.
            if not status_lower.startswith("no dce"):
                return False

        if self.act_limit_manual.isChecked():
            if not is_manual:
                return False

        # Note: Experimental and Deprecated checks are Universe checks. 
        # If the metric is hidden by these flags, it should not be shown even if it matches search.
        if not self.is_metric_in_universe(metric):
            return False

        if prot_count == 0 and group_count == 0:
            return True

        if prot_count > 0:
            if metric.protocol_machine_code not in sel_protocols:
                return False
        
        if group_count > 0:
            m_groups = getattr(metric, 'hierarchy', [])
            if m_groups:
                if not any(g in sel_groups for g in m_groups):
                    return False
        
        return True

    def is_metric_in_universe(self, metric):
        
        # Check Protocol Status first
        protocol_status = 'active'
        protocol_experimental = False
        for p in self.qris_project.protocols.values():
            if p.machine_code == metric.protocol_machine_code:
                if "experimental" in p.name.lower() or getattr(p, 'status', 'active') == 'experimental':
                    protocol_experimental = True
                
                if getattr(p, 'status', 'active') == 'deprecated':
                    protocol_status = 'deprecated'
                break

        if not self.act_include_experimental.isChecked():
             if protocol_experimental:
                 return False

        if not self.act_include_deprecated.isChecked():
            status = getattr(metric, 'status', 'active')
            if status == 'deprecated' or protocol_status == 'deprecated':
                return False
        
        return True

    def clear_filters(self):
        self.txt_filter_search.clear()
        self.cbo_filter_protocol.set_all_check_state(QtCore.Qt.Checked)
        # Groups will be reset by protocol change triggers usually, but explicit is better
        self.cbo_filter_group.set_all_check_state(QtCore.Qt.Checked)
        
        self.act_limit_metrics.setChecked(False)
        self.act_show_all.setChecked(True) # Resets the exclusive group to "All"
        # Do not reset Universe filters (Experimental/Deprecated) as they are likely user preferences
        
        self.update_visibility()

    def update_visibility(self):
        # Update currently active view only? Or both?
        # Better both so switching is instant.

        # Calculate Universe Count (Y)
        all_metrics = self.qris_project.metrics.values()
        universe_count = sum(1 for m in all_metrics if self.is_metric_in_universe(m))
        
        # 1. Update Tree Transparency
        root = self.metricsTree.invisibleRootItem()
        for i in range(root.childCount()):
            prot_item = root.child(i)
            prot_visible = False
            
            for j in range(prot_item.childCount()):
                group_or_metric = prot_item.child(j)
                self.update_tree_item_visibility(group_or_metric)
                if not group_or_metric.isHidden():
                    prot_visible = True
            
            prot_item.setHidden(not prot_visible)

        # 2. Update Table Transparency
        visible_count = 0
        for row in range(self.metricsTable.rowCount()):
             item = self.metricsTable.item(row, 0)
             metric = item.data(QtCore.Qt.UserRole)
             if metric:
                 show = self.should_show_metric(metric)
                 self.metricsTable.setRowHidden(row, not show)
                 if show:
                     visible_count += 1
        
        self.lbl_filter_count.setText(f"Viewing {visible_count} of {universe_count} Metrics")

    def update_tree_item_visibility(self, item):
        # Leaf node check
        metric = item.data(0, QtCore.Qt.UserRole)
        if metric:
            # It's a metric leaf
            visible = self.should_show_metric(metric)
            item.setHidden(not visible)
            return visible
        
        # It's a group node
        any_child_visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_visible = self.update_tree_item_visibility(child) # Recursion
            if child_visible:
                any_child_visible = True
        
        item.setHidden(not any_child_visible)
        return any_child_visible

    def load_current_view(self):
        self.update_visibility()
        self.update_usage_count_label()

    def load_metrics_tree(self):
        pass # Replaced by build_metrics_tree called once

    def build_metrics_tree(self):
        self.metricsTree.setSortingEnabled(False)
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
            
            font = self.get_metric_font(metric, level_id)
            metric_item.setFont(0, font)
            
            # Version (Status)
            status = getattr(metric, 'status', 'active')
            ver_text = str(metric.version) if metric.version else ""
            metric_item.setText(1, f"{ver_text} ({status})")
            metric_item.setFont(1, font)

            # Availability
            calc_status = metric.get_automation_availability(self.qris_project, self.analysis_metadata)
            metric_item.setText(2, calc_status)

            # Usage
            usage_display = ['None', 'Metric', 'Indicator'][level_id] if 0 <= level_id <= 2 else 'None'
            
            # Use a specialized item for sorting if feasible, or just text
            # Setting text on column 4 allows sorting even if widget covers it?
            # QTreeWidget uses the item text for sorting.
            metric_item.setText(3, usage_display)

            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            cboStatus.setProperty("metric_item", metric_item) 
            cboStatus.currentIndexChanged.connect(lambda idx, m_id=metric.id: self.on_metric_status_changed(m_id, idx))
            self.metricsTree.setItemWidget(metric_item, 3, cboStatus)

            # Description
            metric_item.setText(4, metric.description)
            metric_item.setToolTip(4, metric.description)
        
        self.metricsTree.setSortingEnabled(True)

    def open_tree_context_menu(self, position):
        item = self.metricsTree.itemAt(position)
        if not item: return

        metric = item.data(0, QtCore.Qt.UserRole)
        if not metric: return

        menu = QtWidgets.QMenu()
        action_details = menu.addAction("Metric Details...")
        action_details.triggered.connect(lambda: FrmLayerMetricDetails(self, self.qris_project, metric=metric).exec_())

        menu.addSeparator()

        action_matrix = menu.addAction("Automation Availability Matrix...")
        # Use a closure capture to ensure current metadata is passed, not bound at definition time differently? 
        # Actually lambda binding should be fine as long as self.analysis_metadata is updated on 'self'.
        # However, let's explicitely pass self.analysis_metadata at call time
        def open_matrix():
            # QgsMessageLog.logMessage(f"Opening Matrix with Metadata: {self.analysis_metadata}", "QRiS", Qgis.Warning)
            FrmMetricAvailabilityMatrix(self, self.qris_project, metric, self.analysis_metadata, limit_dces=self.limit_dces).exec_()
            
        action_matrix.triggered.connect(open_matrix)
        
        menu.exec_(self.metricsTree.viewport().mapToGlobal(position))

    def load_metrics_table(self):
        pass

    def build_metrics_table(self):
        self.metricsTable.setSortingEnabled(False)
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
            font = self.get_metric_font(metric, level_id)
            label_item.setFont(font)
            self.metricsTable.setItem(row, 2, label_item)
            label_item.setFlags(QtCore.Qt.ItemIsEnabled)

            # Version (Status)
            status = getattr(metric, 'status', 'active')
            ver_text = str(metric.version) if metric.version else ""
            ver_item = QtWidgets.QTableWidgetItem()
            ver_item.setText(f"{ver_text} ({status})")
            ver_item.setFont(font)
            ver_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 3, ver_item)

            # Availability
            calc_status = metric.get_automation_availability(self.qris_project, self.analysis_metadata)
            calc_item = QtWidgets.QTableWidgetItem()
            calc_item.setText(calc_status)
            calc_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.metricsTable.setItem(row, 4, calc_item)

            # Usage
            usage_display = ['None', 'Metric', 'Indicator'][level_id] if 0 <= level_id <= 2 else 'None'
            
            # Create an item for sorting purposes
            usage_item = QtWidgets.QTableWidgetItem(usage_display)
            self.metricsTable.setItem(row, 5, usage_item)

            cboStatus = QtWidgets.QComboBox()
            cboStatus.addItem('None', 0)
            cboStatus.addItem('Metric', 1)
            cboStatus.addItem('Indicator', 2)
            cboStatus.setCurrentIndex(level_id)
            cboStatus.currentIndexChanged.connect(lambda idx, m_id=metric.id: self.on_metric_status_changed(m_id, idx))
            self.metricsTable.setCellWidget(row, 5, cboStatus)

            # Description
            desc_item = QtWidgets.QTableWidgetItem(metric.description)
            desc_item.setFlags(QtCore.Qt.ItemIsEnabled)
            desc_item.setToolTip(metric.description)
            self.metricsTable.setItem(row, 6, desc_item)

        self.metricsTable.resizeColumnsToContents()
        self.metricsTable.setColumnWidth(5, 120) # Ensure Usage column is wide enough for ComboBox
        self.metricsTable.setSortingEnabled(True)

    def open_table_context_menu(self, position):
        item = self.metricsTable.itemAt(position)
        if not item: return
        
        row = item.row()
        metric_item = self.metricsTable.item(row, 0) # Metric stored in first column data
        if not metric_item: return

        metric = metric_item.data(QtCore.Qt.UserRole)
        if not metric: return

        menu = QtWidgets.QMenu()
        action_details = menu.addAction("Metric Details...")
        action_details.triggered.connect(lambda: FrmLayerMetricDetails(self, self.qris_project, metric=metric).exec_())

        menu.addSeparator()

        action_matrix = menu.addAction("Automation Availability Matrix...")
        action_matrix.triggered.connect(lambda: FrmMetricAvailabilityMatrix(self, self.qris_project, metric, self.analysis_metadata, limit_dces=self.limit_dces).exec_())
        
        menu.exec_(self.metricsTable.viewport().mapToGlobal(position))

    def toggle_all_metrics(self, level_id_text: str):
        metrics_update_map = {} # metric_id -> new_level_idx
        
        # Determine target logic
        use_default = (level_id_text == 'Default')
        fixed_target_idx = 0
        if level_id_text == 'Metric': fixed_target_idx = 1
        elif level_id_text == 'Indicator': fixed_target_idx = 2
        
        usage_labels = ['None', 'Metric', 'Indicator']

        # 1. Calculate updates
        for metric in self.qris_project.metrics.values():
             if self.should_show_metric(metric):
                 new_state = metric.default_level_id if use_default else fixed_target_idx
                 metrics_update_map[metric.id] = new_state
                 self.current_metrics_state[metric.id] = new_state

        # 2. Update Tree Widgets
        iterator = QtWidgets.QTreeWidgetItemIterator(self.metricsTree)
        while iterator.value():
            item = iterator.value()
            metric = item.data(0, QtCore.Qt.UserRole)
            if metric and metric.id in metrics_update_map:
                 new_idx = metrics_update_map[metric.id]
                 item.setText(3, usage_labels[new_idx] if 0 <= new_idx <= 2 else 'None') # Update sorting text
                 
                 # Apply Font
                 font = self.get_metric_font(metric, new_idx)
                 item.setFont(0, font)
                 item.setFont(1, font)

                 w = self.metricsTree.itemWidget(item, 3)
                 if isinstance(w, QtWidgets.QComboBox):
                     w.blockSignals(True)
                     w.setCurrentIndex(new_idx)
                     w.blockSignals(False)
            iterator += 1

        # 3. Update Table Widgets
        for row in range(self.metricsTable.rowCount()):
             item = self.metricsTable.item(row, 0) # Protocol column holds valid items? No, row 0 col 0. Checks valid row.
             if not item: continue # Should not happen
             
             # Metric is stored in Column 0 (Protocol) UserRole? YES.
             metric = item.data(QtCore.Qt.UserRole) 
             
             if metric and metric.id in metrics_update_map:
                 new_idx = metrics_update_map[metric.id]
                 usage_display = usage_labels[new_idx] if 0 <= new_idx <= 2 else 'None'

                 # Update sorting text
                 usage_item = self.metricsTable.item(row, 5)
                 if usage_item:
                     usage_item.setText(usage_display)
                 
                 # Apply Font
                 font = self.get_metric_font(metric, new_idx)
                 if self.metricsTable.item(row, 2): self.metricsTable.item(row, 2).setFont(font)
                 if self.metricsTable.item(row, 3): self.metricsTable.item(row, 3).setFont(font)
                     
                 w = self.metricsTable.cellWidget(row, 5)
                 if isinstance(w, QtWidgets.QComboBox):
                     w.blockSignals(True)
                     w.setCurrentIndex(new_idx)
                     w.blockSignals(False)
                     
        self.update_usage_count_label()

    def get_selected_metrics(self):
        analysis_metrics = {}
        # Iterate through project metrics or cache? 
        # Using cache is safer because it reflects the user's latest actions on the UI
        
        for metric_id, level_idx in self.current_metrics_state.items():
            if level_idx > 0:
                 # Need Metric object.
                 metric = self.qris_project.metrics.get(metric_id)
                 if metric:
                     analysis_metrics[metric_id] = AnalysisMetric(metric, level_idx)
        return analysis_metrics

    def update_usage_count_label(self):
        metrics_count = sum(1 for v in self.current_metrics_state.values() if v == 1)
        indicators_count = sum(1 for v in self.current_metrics_state.values() if v == 2)
        total_count = metrics_count + indicators_count
        self.lbl_usage_count.setText(f"{indicators_count} Indicators and {metrics_count} Metrics currently in use for this Analysis ({total_count} Total)")