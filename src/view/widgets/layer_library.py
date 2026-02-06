from typing import Dict, List, Tuple
import os
from qgis.PyQt import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings

from ...model.project import Project
from ...model.layer import Layer
from ...model.protocol import Protocol
from ...model.event import Event, PLANNING_EVENT_TYPE_ID, DCE_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID

from ...QRiS.settings import Settings
from ...QRiS.protocol_parser import ProtocolDefinition, LayerDefinition, load_protocol_definitions
from ..frm_layer_metric_details import FrmLayerMetricDetails
from .checkable_combo_box import CheckableComboBox

ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'
SHOW_EXPERIMENTAL_PROTOCOLS = 'show_experimental_protocols'

class LayerLibraryWidget(QtWidgets.QWidget):

    def __init__(self, parent, project: Project, event_type_id: int, dce_event: Event = None):
        super(LayerLibraryWidget, self).__init__(parent)
        
        self.qris_project = project
        self.event_type_id = event_type_id
        self.dce_event = dce_event
        self.is_tree_view = True
        
        settings = QSettings(ORGANIZATION, APPNAME)
        self.show_experimental = settings.value(SHOW_EXPERIMENTAL_PROTOCOLS, False, bool)

        # Map unique_key -> inclusion status (bool)
        # Unique key structure: "ProtocolMachineCode::ProtocolVersion::LayerID::LayerVersion"
        self.current_layers_state: Dict[str, bool] = {}
        
        # Store definitions loaded from files
        # Key: "ProtocolMachineCode::ProtocolVersion", Value: ProtocolDefinition
        self.protocol_definitions: Dict[str, ProtocolDefinition] = {} 
        
        self.load_definitions()
        self.init_state()

        self.setupUi()
        self.load_filters()
        self.load_current_view()

    def get_layer_unique_key(self, protocol_def: ProtocolDefinition, layer_def: LayerDefinition):
        return f"{protocol_def.machine_code}::{str(protocol_def.version)}::{layer_def.id}::{str(layer_def.version)}"

    @property
    def tree_model(self):
        return self.layersTree.model()

    def add_selected_layers(self, item):
        data = item.data(0, QtCore.Qt.UserRole)
        # Compatibility handling
        if isinstance(data, tuple):
             p, l = data
             key = self.get_layer_unique_key(p, l)
             self.current_layers_state[key] = True
             self.full_refresh_ui()

    def load_definitions(self):
        # Load protocols
        protocols = load_protocol_definitions(os.path.dirname(self.qris_project.project_file), self.show_experimental)

        self.available_layers = [] # List of (ProtocolDefinition, LayerDefinition)

        for p in protocols:
            p_key = f"{p.machine_code}::{p.version}"
            self.protocol_definitions[p_key] = p

            # Filter by event type if needed
            if self.event_type_id == DCE_EVENT_TYPE_ID:
                # Only allow protocols that are explicitly DCE (case-insensitive)
                if not p.protocol_type or p.protocol_type.strip().lower() != 'dce':
                    continue
            elif self.event_type_id == DESIGN_EVENT_TYPE_ID:
                if not p.protocol_type or p.protocol_type.strip().lower() != 'design':
                    continue
            elif self.event_type_id == AS_BUILT_EVENT_TYPE_ID:
                if not p.protocol_type or p.protocol_type.strip().lower() != 'asbuilt':
                    continue

            for l in p.layers:
                self.available_layers.append((p, l))

    def init_state(self):
        # Initialize all to false
        for p, l in self.available_layers:
            key = self.get_layer_unique_key(p, l)
            self.current_layers_state[key] = False

        # If editing an event, set included layers to True
        if self.dce_event:
            for event_layer in self.dce_event.event_layers:
                layer = event_layer.layer
                # Find the matching definition
                # We need to reverse map the project layer to definitions
                # Layer object has protocol info via get_layer_protocol?
                # Actually Layer object only stores ID, we need to look up protocol logic.
                
                # Check stored protocols in project
                # Using Layer.get_layer_protocol() might work if the protocol is in the project
                proj_protocol = layer.get_layer_protocol(self.qris_project.protocols)
                
                if proj_protocol:
                    # Construct key
                    # layer.layer_id matches def.id, layer.layer_version matches def.version
                    key = f"{proj_protocol.machine_code}::{str(proj_protocol.version)}::{layer.layer_id}::{str(layer.layer_version)}"
                    if key in self.current_layers_state:
                         self.current_layers_state[key] = True
                    else:
                        # Maybe legacy or version mismatch? 
                        # Try loose matching or just log warning?
                        pass

    def setupUi(self):
        self.vert_layout = QtWidgets.QVBoxLayout(self)
        # self.vert_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vert_layout)

        # --- Filters ---
        self.horiz_filters = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_filters)

        self.cbo_filter_protocol = CheckableComboBox()
        self.cbo_filter_protocol.setPlaceholderText("All Protocols")
        self.cbo_filter_protocol.setNoneCheckedText("No Protocols Selected")
        self.cbo_filter_protocol.setEmptyText("No Protocols Available")
        self.cbo_filter_protocol.popupClosed.connect(self.update_visibility) # Just update vis directly
        self.horiz_filters.addWidget(self.cbo_filter_protocol)

        self.txt_filter_search = QtWidgets.QLineEdit()
        self.txt_filter_search.setPlaceholderText("Search Layers...")
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

        # Advanced Filters Menu
        self.btn_advanced = QtWidgets.QToolButton()
        self.btn_advanced.setText("Advanced Filters")
        self.btn_advanced.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btn_advanced.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        
        self.menu_advanced = QtWidgets.QMenu(self.btn_advanced)
        
        self.act_limit_included = self.menu_advanced.addAction("Show Only Included Layers")
        self.act_limit_included.setCheckable(True)
        self.act_limit_included.toggled.connect(self.update_visibility)
        
        self.menu_advanced.addSeparator()

        self.act_show_experimental = self.menu_advanced.addAction("Show Experimental Protocols")
        self.act_show_experimental.setCheckable(True)
        self.act_show_experimental.setChecked(self.show_experimental)
        self.act_show_experimental.toggled.connect(self.on_show_experimental_toggled)
        
        self.btn_advanced.setMenu(self.menu_advanced)
        self.horiz_filters.addWidget(self.btn_advanced)

        # --- Stacked Widget (Tree/Table) ---
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.vert_layout.addWidget(self.stackedWidget)

        # Page 0: Tree View
        self.pageTree = QtWidgets.QWidget()
        self.vboxTree = QtWidgets.QVBoxLayout(self.pageTree)
        self.vboxTree.setContentsMargins(0, 0, 0, 0)
        
        self.layersTree = QtWidgets.QTreeWidget()
        self.layersTree.setHeaderLabels(['Layer', '', 'Version', 'Description'])
        self.layersTree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.layersTree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.layersTree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.layersTree.header().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.layersTree.setColumnWidth(1, 30)
        self.layersTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.layersTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.layersTree.customContextMenuRequested.connect(self.open_tree_context_menu)
        # Move Include column (Logical 1) to first visual position
        self.layersTree.header().moveSection(1, 0)
        self.vboxTree.addWidget(self.layersTree)
        self.stackedWidget.addWidget(self.pageTree)

        # Page 1: Table View
        self.pageTable = QtWidgets.QWidget()
        self.vboxTable = QtWidgets.QVBoxLayout(self.pageTable)
        self.vboxTable.setContentsMargins(0, 0, 0, 0)
        
        self.layersTable = QtWidgets.QTableWidget(0, 6)
        self.layersTable.setHorizontalHeaderLabels(['', 'Protocol', 'Group', 'Layer', 'Version', 'Description'])
        self.layersTable.verticalHeader().setVisible(False)
        header = self.layersTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.layersTable.setColumnWidth(0, 30)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.layersTable.setSortingEnabled(True)
        self.vboxTable.addWidget(self.layersTable)
        self.stackedWidget.addWidget(self.pageTable)

        # --- Bottom Buttons ---
        self.horiz_buttons = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_buttons)

        self.cmdToggleView = QtWidgets.QPushButton(self.get_toggle_text())
        self.cmdToggleView.clicked.connect(self.toggle_view)
        self.horiz_buttons.addWidget(self.cmdToggleView)

        self.lbl_included_count = QtWidgets.QLabel("")
        self.horiz_buttons.addWidget(self.lbl_included_count)

        self.horiz_buttons.addStretch()

        self.btn_select_all = QtWidgets.QPushButton("Include All Visible")
        self.btn_select_all.clicked.connect(lambda: self.batch_set_include(True))
        self.horiz_buttons.addWidget(self.btn_select_all)

        self.btn_select_none = QtWidgets.QPushButton("Remove All Visible")
        self.btn_select_none.clicked.connect(lambda: self.batch_set_include(False))
        self.horiz_buttons.addWidget(self.btn_select_none)

        # Build initial views
        self.build_tree()
        self.build_table()
        
        self.stackedWidget.setCurrentIndex(0)

    def get_toggle_text(self):
        return "Switch to Table View" if self.is_tree_view else "Switch to Tree View"

    def toggle_view(self):
        self.is_tree_view = not self.is_tree_view
        self.cmdToggleView.setText(self.get_toggle_text())
        self.stackedWidget.setCurrentIndex(0 if self.is_tree_view else 1)
        self.load_current_view()

    def load_filters(self):
        # Protocols
        unique_protocols = sorted(list(set([p.label for p, l in self.available_layers])))
        
        self.cbo_filter_protocol.clear()
        if unique_protocols:
             self.cbo_filter_protocol.add_command_item("(Select All)", "SELECT_ALL")
             self.cbo_filter_protocol.add_command_item("(Select None)", "SELECT_NONE")
             self.cbo_filter_protocol.insertSeparator(self.cbo_filter_protocol.count())
             
             self.cbo_filter_protocol.addBatchItems([(p, p) for p in unique_protocols])

    def clear_filters(self):
        self.txt_filter_search.clear()
        self.cbo_filter_protocol.set_all_check_state(QtCore.Qt.Checked)
        self.act_limit_included.setChecked(False)
        self.update_visibility()

    def should_show_layer(self, protocol_def: ProtocolDefinition, layer_def: LayerDefinition):
        # 1. Search
        search = self.txt_filter_search.text().lower().strip()
        if search:
            match = (search in layer_def.label.lower() or 
                     search in protocol_def.label.lower() or 
                     (layer_def.hierarchy and any(search in str(h).lower() for h in layer_def.hierarchy)))
            if not match: return False

        # 2. Protocol Filter
        checked_protocols = self.cbo_filter_protocol.get_checked_data()
        # Handle "All" case or empty case? 
        # If checked_protocols is empty due to Select None, then filtering is active
        # But if cbo is empty, it means no protocols.
        if self.cbo_filter_protocol.count() > 0:
            if protocol_def.label not in checked_protocols:
                return False

        # 3. Limit Included
        if self.act_limit_included.isChecked():
            key = self.get_layer_unique_key(protocol_def, layer_def)
            if not self.current_layers_state.get(key, False):
                return False

        return True

    def update_visibility(self):
        # Update Tree
        root = self.layersTree.invisibleRootItem()
        visible_count = 0
        total_count = len(self.available_layers)
        
        for i in range(root.childCount()):
            prot_item = root.child(i)
            prot_visible = False
            
            for j in range(prot_item.childCount()):
                # Check if group or layer
                child = prot_item.child(j)
                child_visible = self.update_tree_item_visibility(child)
                if child_visible:
                    prot_visible = True
            
            prot_item.setHidden(not prot_visible)

        # Update Table
        visible_rows = 0
        for row in range(self.layersTable.rowCount()):
             data = self.layersTable.item(row, 1).data(QtCore.Qt.UserRole)
             if data:
                 p, l, key = data
                 show = self.should_show_layer(p, l)
                 self.layersTable.setRowHidden(row, not show)
                 if show: visible_rows += 1
        
        self.lbl_filter_count.setText(f"Showing {visible_rows} of {total_count} layers")

    def on_show_experimental_toggled(self, checked):
        self.show_experimental = checked
        
        # Reload everything
        self.load_definitions()
        
        # Ensure new layers have state in dictionary
        for p, l in self.available_layers:
            key = self.get_layer_unique_key(p, l)
            if key not in self.current_layers_state:
                self.current_layers_state[key] = False
                
        self.load_filters()
        self.load_current_view()
        self.update_counts()

    def update_tree_item_visibility(self, item):
        data = item.data(0, QtCore.Qt.UserRole)
        if isinstance(data, list) or isinstance(data, tuple):
             # It's a layer leaf: (ProtocolDefinition, LayerDefinition)
             p, l = data
             visible = self.should_show_layer(p, l)
             item.setHidden(not visible)
             return visible
        else:
            # It's a group node or protocol node
            any_visible = False
            for i in range(item.childCount()):
                child = item.child(i)
                if self.update_tree_item_visibility(child):
                    any_visible = True
            item.setHidden(not any_visible)
            return any_visible

    def build_tree(self):
        self.layersTree.clear()
        
        # Helper to find/create nodes
        def get_node(parent, text, data=None):
            for i in range(parent.childCount()):
                if parent.child(i).text(0) == text:
                    return parent.child(i)
            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, text)
            item.setToolTip(0, text)
            item.setExpanded(True)
            if data: item.setData(0, QtCore.Qt.UserRole, data)
            return item

        for p, l in self.available_layers:
            key = self.get_layer_unique_key(p, l)
            is_included = self.current_layers_state[key]

            # Protocol Node
            prot_node = get_node(self.layersTree.invisibleRootItem(), p.label, data="PROTOCOL")
            
            # Group Node
            parent_node = prot_node
            if l.hierarchy:
                if isinstance(l.hierarchy, list):
                    for group_name in l.hierarchy:
                         parent_node = get_node(parent_node, str(group_name), data="GROUP")
                else:
                     parent_node = get_node(parent_node, str(l.hierarchy), data="GROUP")
            
            # Layer Leaf
            layer_node = QtWidgets.QTreeWidgetItem(parent_node)
            layer_node.setText(0, l.label)
            layer_node.setIcon(0, self.get_geom_icon(l.geom_type))
            layer_node.setText(2, str(l.version))
            layer_node.setText(3, l.description or "")
            layer_node.setData(0, QtCore.Qt.UserRole, (p, l))
            
            layer_node.setToolTip(0, l.label)
            layer_node.setToolTip(2, str(l.version))
            layer_node.setToolTip(3, l.description or "")
            
            self.setup_include_widget(self.layersTree, layer_node, 1, key, is_included)
            self.update_item_style(layer_node, is_included)

    def build_table(self):
        self.layersTable.setRowCount(len(self.available_layers))
        self.layersTable.setSortingEnabled(False)
        
        for i, (p, l) in enumerate(self.available_layers):
            key = self.get_layer_unique_key(p, l)
            is_included = self.current_layers_state[key]
            
            # 1: Protocol
            item_prot = QtWidgets.QTableWidgetItem(p.label)
            item_prot.setToolTip(p.label)
            item_prot.setData(QtCore.Qt.UserRole, (p, l, key))
            self.layersTable.setItem(i, 1, item_prot)
            
            # 0: Include (Checkbox)
            self.setup_include_widget(self.layersTable, i, 0, key, is_included)

            # 2: Group
            group_text = ""
            if l.hierarchy:
                if isinstance(l.hierarchy, list):
                    group_text = " > ".join([str(h) for h in l.hierarchy])
                else:
                    group_text = str(l.hierarchy)
            item_grp = QtWidgets.QTableWidgetItem(group_text)
            item_grp.setToolTip(group_text)
            self.layersTable.setItem(i, 2, item_grp)
            
            # 3: Layer
            item_lay = QtWidgets.QTableWidgetItem(l.label)
            item_lay.setIcon(self.get_geom_icon(l.geom_type))
            item_lay.setToolTip(l.label)
            self.layersTable.setItem(i, 3, item_lay)
            
            # 4: Version
            item_ver = QtWidgets.QTableWidgetItem(str(l.version))
            item_ver.setToolTip(str(l.version))
            self.layersTable.setItem(i, 4, item_ver)

            # 5: Description
            desc = l.description or ""
            item_desc = QtWidgets.QTableWidgetItem(desc)
            item_desc.setToolTip(desc)
            self.layersTable.setItem(i, 5, item_desc)
            
            self.update_table_row_style(i, is_included)
            
        self.layersTable.setSortingEnabled(True)

    def get_geom_icon(self, geom_type):
        icon_name = 'layer'
        if geom_type == 'Point':
            icon_name = 'point'
        elif geom_type == 'Linestring':
            icon_name = 'line'
        elif geom_type == 'Polygon':
            icon_name = 'polygon'
        return QtGui.QIcon(f':plugins/qris_toolbar/{icon_name}')

    def setup_include_widget(self, parent_widget, item_or_row, col, key, is_checked):
        # Create a widget with a checkbox centered
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        
        chk = QtWidgets.QCheckBox()
        chk.setChecked(is_checked)
        chk.clicked.connect(lambda checked: self.on_layer_toggled(key, checked))
        
        layout.addWidget(chk)
        
        if isinstance(parent_widget, QtWidgets.QTreeWidget):
             parent_widget.setItemWidget(item_or_row, col, container)
             # Store reference to chk for updates? 
             item_or_row.setData(col, QtCore.Qt.UserRole, chk)
        else:
             parent_widget.setCellWidget(item_or_row, col, container)
             parent_widget.item(item_or_row, 1).setData(QtCore.Qt.UserRole + 1, chk) # Store ref on protocol column item

    def on_layer_toggled(self, key, checked):
        self.current_layers_state[key] = checked
        self.refresh_styles(key)
        self.update_counts()

    def update_counts(self):
        count = sum(1 for v in self.current_layers_state.values() if v)
        self.lbl_included_count.setText(f"{count} Layers Included")

    def refresh_styles(self, key):
        is_included = self.current_layers_state[key]
        
        # Find items in Tree and Table matching key and update style/checkbox
        # Is there a faster way than iterating? probably mapping but simple iteration is robust.
        
        # Update Tree
        root = self.layersTree.invisibleRootItem()
        def visit(item):
            data = item.data(0, QtCore.Qt.UserRole)
            if isinstance(data, tuple): # Leaf
                 p, l = data
                 if self.get_layer_unique_key(p, l) == key:
                     self.update_item_style(item, is_included)
                     # Update Checkbox state if changed programmatically (batch)
                     chk = item.data(1, QtCore.Qt.UserRole)
                     if chk and chk.isChecked() != is_included:
                         chk.blockSignals(True)
                         chk.setChecked(is_included)
                         chk.blockSignals(False)
            
            for i in range(item.childCount()):
                visit(item.child(i))
        
        for i in range(root.childCount()):
            visit(root.child(i))
            
        # Update Table
        self.layersTable.setSortingEnabled(False) # Prevent jumping
        for row in range(self.layersTable.rowCount()):
             data = self.layersTable.item(row, 1).data(QtCore.Qt.UserRole)
             if data:
                 p, l, k = data
                 if k == key:
                     self.update_table_row_style(row, is_included)
                     # Checkbox
                     chk = self.layersTable.item(row, 1).data(QtCore.Qt.UserRole + 1)
                     if chk and chk.isChecked() != is_included:
                         chk.blockSignals(True)
                         chk.setChecked(is_included)
                         chk.blockSignals(False)
        self.layersTable.setSortingEnabled(True)

    def update_item_style(self, item: QtWidgets.QTreeWidgetItem, is_included):
        font = item.font(0)
        font.setBold(is_included)
        item.setFont(0, font)

    def update_table_row_style(self, row, is_included):
        font = self.layersTable.item(row, 1).font()
        font.setBold(is_included)
        for c in range(1, 6): # Protocol to Version
             item = self.layersTable.item(row, c)
             if item: item.setFont(font)

    def batch_set_include(self, include_state):
        # Apply to all VISIBLE items
        # Tree View active?
        if self.is_tree_view:
            root = self.layersTree.invisibleRootItem()
            def recurse(item):
                if item.isHidden(): return
                data = item.data(0, QtCore.Qt.UserRole)
                if isinstance(data, tuple):
                     p, l = data
                     key = self.get_layer_unique_key(p, l)
                     self.current_layers_state[key] = include_state
                for i in range(item.childCount()):
                    recurse(item.child(i))
            for i in range(root.childCount()):
                recurse(root.child(i))
        else:
            for row in range(self.layersTable.rowCount()):
                 if self.layersTable.isRowHidden(row): continue
                 data = self.layersTable.item(row, 0).data(QtCore.Qt.UserRole)
                 if data:
                     p, l, key = data
                     self.current_layers_state[key] = include_state
        
        # Refresh all UI
        self.full_refresh_ui()

    def full_refresh_ui(self):
        # Brute force update of all styles and checkboxes
        for key in self.current_layers_state:
            self.refresh_styles(key)
        self.update_counts()

    def load_current_view(self):
        self.update_visibility()
        self.update_counts()

    def open_tree_context_menu(self, position):
        item = self.layersTree.itemAt(position)
        if not item: return

        data = item.data(0, QtCore.Qt.UserRole)
        
        menu = QtWidgets.QMenu()
        
        if isinstance(data, tuple): # Layer
             p, l = data
             act_details = menu.addAction("Layer Details...")
             act_details.triggered.connect(lambda: self.show_layer_details(p, l))

        else: # Group or Protocol
             act_inc = menu.addAction("Include All Child Layers")
             act_inc.triggered.connect(lambda: self.set_children_state(item, True))
             
             act_rem = menu.addAction("Remove All Child Layers")
             act_rem.triggered.connect(lambda: self.set_children_state(item, False))
        
        if not menu.isEmpty():
             menu.exec_(self.layersTree.viewport().mapToGlobal(position))

    def show_layer_details(self, protocol_def: ProtocolDefinition, layer_def: LayerDefinition):
        # Ensure protocol definition is attached for context
        # FrmLayerMetricDetails can handle LayerDefinition objects if protocol_definition is set
        layer_def.protocol_definition = protocol_def
        frm = FrmLayerMetricDetails(self, self.qris_project, layer_def)
        frm.exec_()

    def set_children_state(self, parent_item, state):
        def recurse(item):
            data = item.data(0, QtCore.Qt.UserRole)
            if isinstance(data, tuple):
                 p, l = data
                 key = self.get_layer_unique_key(p, l)
                 self.current_layers_state[key] = state
            for i in range(item.childCount()):
                recurse(item.child(i))
        
        recurse(parent_item)
        self.full_refresh_ui()

    # API for FrmEvent to retrieve result
    def get_selected_layer_definitions(self, project_layers_cache) -> Tuple[List[Layer], List[Tuple[ProtocolDefinition, LayerDefinition]]]:
        """
        Returns (list_of_existing_project_layers, list_of_new_definitions_to_create)
        project_layers_cache: Dict of existing project layers to resolve against.
        """
        existing_layers = []
        new_definitions = []
        
        # Build cache of existing project layers by unique key
        # We need to map project layers back to the protocol/layer key format
        # This might be tricky without a clear link.
        # But wait, we used the project layer's protocol info in init_state.
        # Let's rebuild that map.
        
        project_layer_map = {}
        for layer in project_layers_cache.values():
             proj_protocol = layer.get_layer_protocol(self.qris_project.protocols)
             if proj_protocol:
                  key = f"{proj_protocol.machine_code}::{proj_protocol.version}::{layer.layer_id}::{layer.layer_version}"
                  project_layer_map[key] = layer
        
        for p, l in self.available_layers:
            key = self.get_layer_unique_key(p, l)
            if self.current_layers_state[key]:
                if key in project_layer_map:
                    existing_layers.append(project_layer_map[key])
                else:
                    new_definitions.append((p, l))
                    
        return existing_layers, new_definitions
