

from qgis.PyQt import QtCore, QtGui, QtWidgets
from ...model.metric import Metric
from ...model.metric_value import MetricValue, load_metric_values
from ...model.analysis_metric import AnalysisMetric
from ...lib.unit_conversion import short_unit_name, distance_units, area_units, ratio_units
from ..frm_layer_metric_details import FrmLayerMetricDetails
from ..frm_metric_availability_matrix import FrmMetricAvailabilityMatrix
# from ..frm_analysis_units import FrmAnalysisUnits

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

class MetricStatusWidget_Labels(QtWidgets.QWidget):
    edit_clicked = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(2,0,2,0)
        self.layout.setSpacing(4)
        
        # 1. Edit Button
        self.btn_edit = QtWidgets.QToolButton()
        self.btn_edit.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/options'))
        self.btn_edit.setAutoRaise(True)
        self.btn_edit.setToolTip("Edit Metric Value")
        self.btn_edit.setFixedSize(20, 20)
        self.btn_edit.clicked.connect(self.edit_clicked)
        self.layout.addWidget(self.btn_edit)
        
        # 2. Source Indicator (M/A)
        self.lbl_source = QtWidgets.QLabel()
        self.lbl_source.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_source.setFixedSize(20, 20)
        font = self.lbl_source.font()
        font.setBold(True)
        self.lbl_source.setFont(font)
        self.layout.addWidget(self.lbl_source)
        
        # 3. Warning Indicator
        self.lbl_warning = QtWidgets.QLabel()
        self.lbl_warning.setFixedSize(20, 20)
        self.lbl_warning.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.lbl_warning)
        
        self.layout.addStretch()
        
    def update_state(self, is_manual, can_automated, feasibility):
        source_text = ""
        source_tooltip = ""
        
        if is_manual is not None:
             if is_manual:
                 source_text = "M"
                 source_tooltip = "Manual Value"
             else:
                 source_text = "A"
                 source_tooltip = "Automated Value"
        
        self.lbl_source.setText(source_text)
        self.lbl_source.setToolTip(source_tooltip)
        
        # Warning Logic
        icon = None
        tooltip = ""
        if feasibility:
            f_status = feasibility.get('status', 'FEASIBLE')
            f_reasons = feasibility.get('reasons', [])
            if f_status == 'NOT_FEASIBLE' or f_status == 'FEASIBLE_EMPTY':
                 icon_std = QtWidgets.QStyle.SP_MessageBoxWarning if f_status == 'NOT_FEASIBLE' else QtWidgets.QStyle.SP_MessageBoxInformation
                 icon = QtWidgets.QApplication.style().standardIcon(icon_std)
                 msgs = ["Automation Not Feasible:" if f_status == 'NOT_FEASIBLE' else "Automation Feasible (Input Data Empty):"]
                 msgs.extend([f" - {r}" for r in f_reasons])
                 tooltip = "\n".join(msgs)
        
        if icon:
            self.lbl_warning.setPixmap(icon.pixmap(16, 16))
        else:
            self.lbl_warning.clear()
        self.lbl_warning.setToolTip(tooltip)


class MetricStatusWidget_Buttons(QtWidgets.QWidget):
    manual_clicked = QtCore.pyqtSignal()
    automated_clicked = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(2,0,2,0)
        self.layout.setSpacing(2)
        
        # Style for darker highlight on checked state
        btn_style = """
            QToolButton:checked {
                background-color: #bcbcbc;
                border: 1px solid #808080;
                border-radius: 2px;
            }
        """
        
        # 1. Manual Button (Edit/Pencil)
        self.btn_manual = QtWidgets.QToolButton()
        self.btn_manual.setStyleSheet(btn_style)
        self.btn_manual.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/options'))
        self.btn_manual.setAutoRaise(True)
        self.btn_manual.setCheckable(True)
        self.btn_manual.setToolTip("Edit Manual Value")
        self.btn_manual.setFixedSize(22, 22)
        self.btn_manual.clicked.connect(self.manual_clicked)
        self.layout.addWidget(self.btn_manual)
        
        # 2. Automated Button (Calculate)
        self.btn_automated = QtWidgets.QToolButton()
        self.btn_automated.setStyleSheet(btn_style)
        self.btn_automated.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/calculate'))
        self.btn_automated.setAutoRaise(True)
        self.btn_automated.setCheckable(True)
        self.btn_automated.setToolTip("Calculate Automated Value")
        self.btn_automated.setFixedSize(22, 22)
        self.btn_automated.clicked.connect(self.automated_clicked)
        self.layout.addWidget(self.btn_automated)
        
        # 3. Warning Indicator
        self.lbl_warning = QtWidgets.QLabel()
        self.lbl_warning.setFixedSize(20, 20)
        self.lbl_warning.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.lbl_warning)
        
        self.layout.addStretch()

    def update_state(self, is_manual, can_automated, feasibility):
        self.btn_manual.blockSignals(True)
        self.btn_automated.blockSignals(True)
        
        if is_manual is None:
             self.btn_manual.setChecked(False)
             self.btn_automated.setChecked(False)
        else:
            self.btn_manual.setChecked(is_manual)
            self.btn_automated.setChecked(not is_manual)
            
        self.btn_manual.blockSignals(False)
        self.btn_automated.blockSignals(False)
        
        # Feasibility / Enabled Logic
        f_status = feasibility.get('status', 'FEASIBLE') if feasibility else 'FEASIBLE'
        tooltip = "Calculate Automated Value"
        if f_status == 'MANUAL_ONLY':
             tooltip = "Manual Only Metric"
        elif f_status == 'NOT_FEASIBLE':
             tooltip = "Calculation Not Feasible"
        elif f_status == 'FEASIBLE_EMPTY':
             tooltip = "Calculate (Input Data Empty)"
             
        self.btn_automated.setEnabled(can_automated)
        self.btn_automated.setToolTip(tooltip)
        
        # Warning Logic
        icon = None
        warning_tooltip = ""
        if f_status == 'NOT_FEASIBLE' or f_status == 'FEASIBLE_EMPTY':
             f_reasons = feasibility.get('reasons', [])
             icon_std = QtWidgets.QStyle.SP_MessageBoxWarning if f_status == 'NOT_FEASIBLE' else QtWidgets.QStyle.SP_MessageBoxInformation
             icon = QtWidgets.QApplication.style().standardIcon(icon_std)
             msgs = ["Automation Not Feasible:" if f_status == 'NOT_FEASIBLE' else "Automation Feasible (Input Data Empty):"]
             msgs.extend([f" - {r}" for r in f_reasons])
             warning_tooltip = "\n".join(msgs)
        
        if icon:
            self.lbl_warning.setPixmap(icon.pixmap(16, 16))
        else:
            self.lbl_warning.clear()
        self.lbl_warning.setToolTip(warning_tooltip)

class AnalysisTable(QtWidgets.QWidget):

    metric_edit_requested = QtCore.pyqtSignal(object)
    metric_calculate_requested = QtCore.pyqtSignal(object, object)

    column = {
        'status': 0,
        'protocol': 1,
        'metric': 2,
        'value': 3,
        'units': 4,
        'uncertainty': 5
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.qris_project = None
        self.analysis = None
        self.current_dce = None
        self.mask_feature_id = None
        self.layout_mode = "Buttons" # "Labels" or "Buttons"
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        # Create Main Layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Create Header Layout for Filters
        self.header_layout_filters = QtWidgets.QHBoxLayout()
        
        self.cbo_filter_protocol = CheckableComboBox()
        self.cbo_filter_protocol.setPlaceholderText("All Protocols")
        self.cbo_filter_protocol.setNoneCheckedText("No Protocols Selected")
        self.cbo_filter_protocol.setEmptyText("No Protocols Available")
        self.header_layout_filters.addWidget(self.cbo_filter_protocol)

        self.txt_filter_search = QtWidgets.QLineEdit()
        self.txt_filter_search.setPlaceholderText("Search Metrics...")
        self.header_layout_filters.addWidget(self.txt_filter_search)

        self.btn_clear_filters = QtWidgets.QPushButton()
        self.btn_clear_filters.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/clear_filter'))
        self.btn_clear_filters.setToolTip("Clear Filters")
        self.header_layout_filters.addWidget(self.btn_clear_filters)

        self.header_layout_filters.addStretch()

        self.btn_advanced = QtWidgets.QToolButton()
        self.btn_advanced.setText("Advanced Filters")
        self.btn_advanced.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btn_advanced.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.header_layout_filters.addWidget(self.btn_advanced)

        self.main_layout.addLayout(self.header_layout_filters)

        # Create Table Widget
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setHorizontalHeaderLabels(['', 'Protocol', 'Metric', 'Value', 'Units', 'Uncertainty'])
        self.table.setColumnHidden(self.column['protocol'], True)
        
        self.table.horizontalHeader().setSectionResizeMode(self.column['status'], QtWidgets.QHeaderView.Fixed) 
        self.table.horizontalHeader().setSectionResizeMode(self.column['uncertainty'], QtWidgets.QHeaderView.Fixed)
        self.table.setColumnWidth(self.column['status'], 80)
        self.table.setColumnWidth(self.column['units'], 75)
        self.table.setColumnWidth(self.column['value'], 100)
        self.table.setColumnWidth(self.column['uncertainty'], 100)
        self.table.setIconSize(QtCore.QSize(16, 16))
        
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        self.main_layout.addWidget(self.table)

        # Display Controls Layout
        self.layoutDisplay = QtWidgets.QHBoxLayout()
        
        # Testing Switcher
        self.lblTestOption = QtWidgets.QLabel("Testing Option:")
        self.layoutDisplay.addWidget(self.lblTestOption)
        
        self.cboTestOption = QtWidgets.QComboBox()
        self.cboTestOption.addItems(["A: Labels", "B: Buttons"])
        self.cboTestOption.setCurrentText("B: Buttons")
        self.cboTestOption.currentTextChanged.connect(self.on_switch_layout_mode)
        self.layoutDisplay.addWidget(self.cboTestOption)
        
        self.layoutDisplay.addStretch()
        self.btnUnits = QtWidgets.QToolButton()
        self.btnUnits.setText('Units')
        self.btnUnits.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btnUnits.setToolTip('Change metric display units')
        self.layoutDisplay.addWidget(self.btnUnits)
        
        self.main_layout.addLayout(self.layoutDisplay)

    def connect_signals(self):
        self.table.itemClicked.connect(self.on_item_clicked)
        self.table.doubleClicked.connect(self.on_item_double_clicked)
        self.cbo_filter_protocol.popupClosed.connect(self.filter_rows)
        self.txt_filter_search.textChanged.connect(self.filter_rows)
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        self.setup_advanced_filters()
        self.setup_units_menu()

    def setup_advanced_filters(self):
        self.menu_advanced = QtWidgets.QMenu(self.btn_advanced)
        
        self.act_limit_indicators = self.menu_advanced.addAction("Limit to Indicators Only")
        self.act_limit_indicators.setCheckable(True)
        self.act_limit_indicators.toggled.connect(self.filter_rows)

        self.menu_advanced.addSeparator()

        self.act_limit_automated = self.menu_advanced.addAction("Limit to Automated Calculations")
        self.act_limit_automated.setCheckable(True)
        self.act_limit_automated.toggled.connect(self.filter_rows)
        
        self.act_limit_manual = self.menu_advanced.addAction("Limit to Manual Only Calculations")
        self.act_limit_manual.setCheckable(True)
        self.act_limit_manual.toggled.connect(self.filter_rows)
        
        # Mutual Exclusivity for Type
        self.act_limit_automated.toggled.connect(lambda checked: self.act_limit_manual.setChecked(False) if checked else None)
        self.act_limit_manual.toggled.connect(lambda checked: self.act_limit_automated.setChecked(False) if checked else None)

        self.menu_advanced.addSeparator()

        self.act_limit_not_calculated = self.menu_advanced.addAction("Limit to Not Calculated")
        self.act_limit_not_calculated.setCheckable(True)
        self.act_limit_not_calculated.toggled.connect(self.filter_rows)
        
        self.act_limit_values = self.menu_advanced.addAction("Limit to Values Only")
        self.act_limit_values.setCheckable(True)
        self.act_limit_values.toggled.connect(self.filter_rows)
        
        self.btn_advanced.setMenu(self.menu_advanced)

    def setup_units_menu(self):
        menu = QtWidgets.QMenu(self)
        
        # Distance Units
        dist_menu = menu.addMenu('Distance')
        self.dist_actions = {}
        ag_dist = QtWidgets.QActionGroup(self)
        for unit_name in distance_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='distance', u=unit_name: self.update_unit(t, u))
            dist_menu.addAction(action)
            ag_dist.addAction(action)
            self.dist_actions[unit_name] = action

        # Area Units
        area_menu = menu.addMenu('Area')
        self.area_actions = {}
        ag_area = QtWidgets.QActionGroup(self)
        for unit_name in area_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='area', u=unit_name: self.update_unit(t, u))
            area_menu.addAction(action)
            ag_area.addAction(action)
            self.area_actions[unit_name] = action

        # Ratio Units
        ratio_menu = menu.addMenu('Ratio')
        self.ratio_actions = {}
        ag_ratio = QtWidgets.QActionGroup(self)
        for unit_name in ratio_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='ratio', u=unit_name: self.update_unit(t, u))
            ratio_menu.addAction(action)
            ag_ratio.addAction(action)
            self.ratio_actions[unit_name] = action

        menu.aboutToShow.connect(self.update_menu_state)
        self.btnUnits.setMenu(menu)

    def update_menu_state(self):
        if not self.analysis:
            return
        
        current_dist = self.analysis.units.get('distance')
        if current_dist in self.dist_actions:
            self.dist_actions[current_dist].setChecked(True)

        current_area = self.analysis.units.get('area')
        if current_area in self.area_actions:
            self.area_actions[current_area].setChecked(True)
            
        current_ratio = self.analysis.units.get('ratio')
        if current_ratio in self.ratio_actions:
            self.ratio_actions[current_ratio].setChecked(True)

    def update_unit(self, unit_type, unit_name):
        if self.analysis:
            self.analysis.units[unit_type] = unit_name
            self.build_table()
            self.load_values(self.current_dce, self.mask_feature_id)

    def configure(self, qris_project, analysis):
        self.qris_project = qris_project
        self.analysis = analysis
        self.load_protocols()

    def load_protocols(self):
        self.cbo_filter_protocol.clear()
        
        if self.qris_project and hasattr(self.qris_project, 'protocols'):
            # Filter protocols to those used in the analysis (if analysis is loaded)
            relevant_protocols = []
            if self.analysis:
                used_codes = set()
                for am in self.analysis.analysis_metrics.values():
                    used_codes.add(am.metric.protocol_machine_code)
                
                for p in self.qris_project.protocols.values():
                    if p.machine_code in used_codes:
                        relevant_protocols.append(p)
            else:
                relevant_protocols = list(self.qris_project.protocols.values())

            protocols = sorted(relevant_protocols, key=lambda p: p.name)
            
            # Add Commands
            self.cbo_filter_protocol.add_command_item("Select All", "SELECT_ALL")
            self.cbo_filter_protocol.add_command_item("Select None", "SELECT_NONE")
            
            # Add Items
            items = []
            for p in protocols:
                items.append((p.name, p.machine_code))
            
            self.cbo_filter_protocol.addBatchItems(items)

    def filter_rows(self):
        search_text = self.txt_filter_search.text().lower()
        selected_protocols = self.cbo_filter_protocol.get_checked_data()
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.column['metric'])
            if not item:
                continue
            analysis_metric = item.data(QtCore.Qt.UserRole)
            if not analysis_metric:
                continue
            metric = analysis_metric.metric
            
            match_search = search_text in metric.name.lower()
            match_protocol = True
            if selected_protocols:
                match_protocol = metric.protocol_machine_code in selected_protocols

            # Advanced Filters (Display)
            match_display = True
            if self.act_limit_indicators.isChecked():
                if analysis_metric.level_id != 2:
                    match_display = False

            # Advanced Filters (Metadata Based)
            match_type = True
            if self.act_limit_automated.isChecked():
                if metric.metric_function is None:
                    match_type = False
            elif self.act_limit_manual.isChecked():
                if metric.metric_function is not None:
                    match_type = False

            # Advanced Filters (Value Based)
            match_value_state = True
            metric_value = self.table.item(row, self.column['value']).data(QtCore.Qt.UserRole)
            
            # Determine Value States
            has_automated_value = False
            is_null_value = True

            if metric_value:
                has_automated_value = metric_value.automated_value is not None
                
                # Determine effective null state (mirroring set_status logic somewhat)
                val = None
                if metric_value.is_manual == 1 and metric_value.manual_value is not None:
                    val = metric_value.manual_value
                else:
                    val = metric_value.automated_value
                
                is_null_value = val is None

            if self.act_limit_not_calculated.isChecked():
                if has_automated_value:
                    match_value_state = False
            
            if self.act_limit_values.isChecked():
                if is_null_value:
                    match_value_state = False
            
            self.table.setRowHidden(row, not (match_search and match_protocol and match_display and match_type and match_value_state))

    def clear_filters(self):
        self.txt_filter_search.clear()
        self.cbo_filter_protocol.set_all_check_state(QtCore.Qt.Checked)
        
        self.act_limit_indicators.setChecked(False)
        self.act_limit_automated.setChecked(False)
        self.act_limit_manual.setChecked(False)
        self.act_limit_not_calculated.setChecked(False)
        self.act_limit_values.setChecked(False)

        self.filter_rows()

    def build_table(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        
        if self.analysis is None:
            return

        analysis_metrics = list(self.analysis.analysis_metrics.values())
        self.table.setRowCount(len(analysis_metrics))
        for row in range(len(analysis_metrics)):
            self.create_row(row, analysis_metrics[row])
        
        self.table.resizeColumnToContents(self.column['metric'])
        self.filter_rows()
    
    def on_switch_layout_mode(self, text):
        if "Labels" in text:
            self.layout_mode = "Labels"
        else:
            self.layout_mode = "Buttons"
        self.build_table()
        self.load_values(self.current_dce, self.mask_feature_id)

    def create_row(self, row, analysis_metric: AnalysisMetric):
        metric: Metric = analysis_metric.metric
        
        # Status Widget
        if self.layout_mode == "Labels":
            status_widget = MetricStatusWidget_Labels()
            status_widget.edit_clicked.connect(lambda: self._handle_edit(row))
        else:
            status_widget = MetricStatusWidget_Buttons()
            status_widget.manual_clicked.connect(lambda: self._handle_edit(row))
            status_widget.automated_clicked.connect(lambda: self._handle_calculate(row))
            
        self.table.setCellWidget(row, self.column['status'], status_widget)
        
        protocol_name = metric.protocol_machine_code
        if self.qris_project and metric.protocol_machine_code in self.qris_project.protocols:
            protocol_name = self.qris_project.protocols[metric.protocol_machine_code].name
        
        label_protocol = QtWidgets.QTableWidgetItem(protocol_name)
        self.table.setItem(row, self.column['protocol'], label_protocol)
    
        label_metric = QtWidgets.QTableWidgetItem()
        label_metric.setText(metric.name)
        self.table.setItem(row, self.column['metric'], label_metric)
        label_metric.setData(QtCore.Qt.UserRole, analysis_metric)

        label_units = QtWidgets.QTableWidgetItem()
        display_unit = short_unit_name(self.analysis.units.get(metric.unit_type, None))
        if metric.normalized:
            if display_unit != 'ratio':
                normalization_unit = self.analysis.units['distance'] 
                display_unit = f'{display_unit}/{short_unit_name(normalization_unit)}'
        label_units.setText(display_unit)
        self.table.setItem(row, self.column['units'], label_units)           

        label_value = QtWidgets.QTableWidgetItem()
        self.table.setItem(row, self.column['value'], label_value)

        label_uncertainty = QtWidgets.QTableWidgetItem()
        self.table.setItem(row, self.column['uncertainty'], label_uncertainty)

    def load_values(self, event, mask_feature_id):
        self.current_dce = event
        self.mask_feature_id = mask_feature_id

        if event is not None and mask_feature_id is not None and self.qris_project is not None:
            # Load latest metric values from DB
            metric_values = load_metric_values(self.qris_project.project_file, self.analysis, event, mask_feature_id, self.qris_project.metrics)

            # Loop over active metrics and load values into grid
            for row in range(self.table.rowCount()):
                analysis_metric: AnalysisMetric = self.table.item(row, self.column['metric']).data(QtCore.Qt.UserRole)
                metric: Metric = analysis_metric.metric
                
                # Update Status Widget (Source)
                status_widget = self.table.cellWidget(row, self.column['status'])
                
                metric_value = None
                metric_value_text = 'null'
                uncertainty_text = ''
                
                is_manual = None # Unknown
                has_automated = False
                
                if metric.id in metric_values:
                    metric_value = metric_values[metric.id]
                    display_unit = self.analysis.units.get(metric.unit_type, None)
                    if metric.normalized:
                        if display_unit != 'ratio':
                            display_unit = self.analysis.units['distance']
                    display_unit = None if display_unit in ['count', 'ratio'] else display_unit
                    metric_value_text = metric_value.current_value_as_string(display_unit)
                    uncertainty_text = metric_value.uncertainty_as_string()
                    
                    is_manual = metric_value.is_manual
                    has_automated = metric_value.automated_value is not None

                self.table.item(row, self.column['value']).setData(QtCore.Qt.UserRole, metric_value)
                self.table.item(row, self.column['value']).setText(metric_value_text)
                self.table.item(row, self.column['uncertainty']).setText(uncertainty_text)
                
                # Check Feasibility
                feasibility = self.analysis.check_metric_feasibility(metric, self.qris_project, self.current_dce)
                
                if status_widget:
                    status_widget.update_state(is_manual, has_automated, feasibility)

                # self.set_status(row, feasibility) # Handled by update_state now
                
        self.table.resizeColumnToContents(self.column['metric'])
        self.filter_rows()

    # set_status method removed (logic moved to widget classes)

    def _handle_calculate(self, row):
        analysis_metric = self.table.item(row, self.column['metric']).data(QtCore.Qt.UserRole)
        metric_value = self.table.item(row, self.column['value']).data(QtCore.Qt.UserRole)
        self.metric_calculate_requested.emit(analysis_metric, metric_value)

    def on_item_clicked(self, item):
        # Edit handling is now done via signal from widget
        pass

    def on_item_double_clicked(self, item):
        self._handle_edit(item.row())

    def on_item_double_clicked(self, item):
        self._handle_edit(item.row())

    def open_context_menu(self, position):
        item = self.table.itemAt(position)
        if not item: return

        row = item.row()
        metric_item = self.table.item(row, self.column['metric'])
        if not metric_item: return

        analysis_metric = metric_item.data(QtCore.Qt.UserRole)
        if not analysis_metric: return
        metric = analysis_metric.metric

        menu = QtWidgets.QMenu()
        action_details = menu.addAction("Metric Details...")
        action_details.triggered.connect(lambda: FrmLayerMetricDetails(self, self.qris_project, metric=metric).exec_())

        menu.addSeparator()

        analysis_metadata = self.analysis.metadata.copy() if self.analysis and self.analysis.metadata else {}
        
        current_dce_id = self.current_dce.id if self.current_dce else None
        
        action_matrix = menu.addAction("Automation Availability Matrix...")
        action_matrix.triggered.connect(lambda: FrmMetricAvailabilityMatrix(self, self.qris_project, metric, analysis_metadata, highlight_dce_id=current_dce_id).exec_())
        
        menu.addSeparator()

        # Copy Value Actions
        val_item = self.table.item(row, self.column['value'])
        if val_item and val_item.text() != "null":
            value_text = val_item.text()
            
            action_copy_val = menu.addAction("Copy Value")
            action_copy_val.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(value_text.strip()))
            
            action_copy_val_units = menu.addAction("Copy Value with Units")
            units_text = self.table.item(row, self.column['units']).text()
            
            # Logic to handle unit display text
            clipboard_text = f"{value_text.strip()} {units_text}"
            if units_text.lower() in ['ratio', 'count']:
                clipboard_text = value_text.strip()
            
            action_copy_val_units.triggered.connect(lambda chk, t=clipboard_text: QtWidgets.QApplication.clipboard().setText(t))

        menu.exec_(self.table.viewport().mapToGlobal(position))

    def _handle_edit(self, row):
        metric_value = self.table.item(row, self.column['value']).data(QtCore.Qt.UserRole)
        if metric_value is None:
            metric: Metric = self.table.item(row, self.column['metric']).data(QtCore.Qt.UserRole).metric
            metric_value = MetricValue(metric, None, None, True, None, None, metric.default_unit_id, {})
        
        self.metric_edit_requested.emit(metric_value)
