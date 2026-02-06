from qgis.PyQt import QtWidgets, QtCore, QtGui

from ...model.event import Event, DCE_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID
from ...model.project import Project
from .checkable_combo_box import CheckableComboBox

class SortableTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __lt__(self, other):
        return (self.data(QtCore.Qt.UserRole) or "") < (other.data(QtCore.Qt.UserRole) or "")

class ReorderableTableWidget(QtWidgets.QTableWidget):
    """
    A QTableWidget that supports drag-and-drop row reordering without jumbling columns.
    """
    orderChanged = QtCore.pyqtSignal()

    def dropEvent(self, event):
        if event.source() == self and (event.dropAction() == QtCore.Qt.MoveAction or self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove):
            
            selection = self.selectedItems()
            if not selection:
                return
            
            drag_rows = sorted(list(set(item.row() for item in selection)))
            drop_index = self.indexAt(event.pos())
            target_row = drop_index.row() if drop_index.isValid() else self.rowCount()
            
            if drop_index.isValid():
                rect = self.visualRect(drop_index)
                if event.pos().y() > rect.center().y():
                    target_row += 1

            moved_rows_data = []
            
            self.blockSignals(True)
            try:
                for row in drag_rows:
                    row_cols = []
                    for col in range(self.columnCount()):
                        row_cols.append(self.takeItem(row, col))
                    moved_rows_data.append(row_cols)
                
                rows_before_target = len([r for r in drag_rows if r < target_row])
                insert_row = target_row - rows_before_target
                
                for row in reversed(drag_rows):
                    self.removeRow(row)
                    
                for i, row_data in enumerate(moved_rows_data):
                    self.insertRow(insert_row + i)
                    for col, item in enumerate(row_data):
                        self.setItem(insert_row + i, col, item)
                
                self.clearSelection()
                for i in range(len(moved_rows_data)):
                    self.selectRow(insert_row + i)
            finally:
                self.blockSignals(False)

            event.accept()
            self.orderChanged.emit()
            
        else:
            super().dropEvent(event)


class EventLibraryWidget(QtWidgets.QWidget):
    # Implement a Event Library grid picker, which loads events in event library, exposes their date, and type (columns) allows sorting), and has a checkbox 

    # signal emitted when the user checks or unchecks an event
    event_checked = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, event_types: list=None, allow_reorder: bool=False):
        super().__init__(parent)
        self.qris_project = qris_project
        self.limit_event_types = event_types
        self.allow_reorder = allow_reorder
        
        # State
        self.all_events = [] 
        self.checked_event_ids = set()

        self.setupUi()
        self.load_events()

    def get_icon_alias(self, type_id):
        if type_id == DCE_EVENT_TYPE_ID: return "calendar"
        if type_id == DESIGN_EVENT_TYPE_ID: return "design"
        if type_id == AS_BUILT_EVENT_TYPE_ID: return "as-built"
        return None

    def load_events(self, events: list = None):
        if events is None:
            raw_events = list(self.qris_project.events.values())
        else:
            raw_events = events

        if self.limit_event_types is not None:
            self.all_events = [e for e in raw_events if e.event_type.id in self.limit_event_types]
        else:
            self.all_events = raw_events
        
        # Init Filters
        self.init_filters()
        self.refresh_table_view()

    def init_filters(self):
        # Sort so "Generic Data Capture Event" (DCE) is first
        types = sorted(list(set(e.event_type.name for e in self.all_events)))
        if "Generic Data Capture Event" in types:
            types.remove("Generic Data Capture Event")
            types.insert(0, "Generic Data Capture Event")

        self.cbo_filter_type.blockSignals(True)
        self.cbo_filter_type.clear()
        
        if types:
            self.cbo_filter_type.add_command_item("Select All", "SELECT_ALL")
            self.cbo_filter_type.add_command_item("Select None", "SELECT_NONE")

        for t in types:
            self.cbo_filter_type.addItem(t)
        self.cbo_filter_type.blockSignals(False)

    def refresh_table_view(self):
        search_text = self.txt_filter_search.text().lower().strip()
        checked_types = self.cbo_filter_type.get_checked_items()
        
        # If we have modified the table order manually (via drag/drop), we might lose that order here if we purely rebuild from all_events.
        # But syncing the list is complex. We accept reset on filter change.
        
        filtered_events = []
        for e in self.all_events:
            if search_text and search_text not in e.name.lower():
                continue
            if e.event_type.name not in checked_types:
                continue
            filtered_events.append(e)

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(filtered_events))
        
        for i, event in enumerate(filtered_events):
            # 0: Checkbox
            checkItem = QtWidgets.QTableWidgetItem()
            checkItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            if event.id in self.checked_event_ids:
                checkItem.setCheckState(QtCore.Qt.Checked)
            else:
                checkItem.setCheckState(QtCore.Qt.Unchecked)
            self.table.setItem(i, 0, checkItem)
            
            # 1: Name + Icon
            item = QtWidgets.QTableWidgetItem(event.name)
            item.setData(QtCore.Qt.UserRole, event) # Store event object
            icon_alias = self.get_icon_alias(event.event_type.id)
            if icon_alias:
                item.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/{icon_alias}'))
            self.table.setItem(i, 1, item)
            
            # 2: Date
            date_item = SortableTableWidgetItem(event.date)
            sort_key = (0,0,0)
            if event.start:
                sort_key = (event.start.year or 0, event.start.month or 0, event.start.day or 0)
            date_item.setData(QtCore.Qt.UserRole, sort_key)
            self.table.setItem(i, 2, date_item)

            # 3: Type
            type_item = QtWidgets.QTableWidgetItem(event.event_type.name)
            self.table.setItem(i, 3, type_item)

            # 4: Description
            desc_item = QtWidgets.QTableWidgetItem(event.description or "")
            self.table.setItem(i, 4, desc_item)
        
        self.table.setColumnWidth(0, 30)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)
        
        self.update_summary()

    def update_summary(self):
        visible_count = self.table.rowCount()
        total_count = len(self.all_events)
        self.lbl_view_count.setText(f"Viewing {visible_count} of {total_count} Events")
        
        sel_events = self.get_selected_events_objects()
        
        dce_count = sum(1 for e in sel_events if e.event_type.id == DCE_EVENT_TYPE_ID)
        design_count = sum(1 for e in sel_events if e.event_type.id == DESIGN_EVENT_TYPE_ID)
        asbuilt_count = sum(1 for e in sel_events if e.event_type.id == AS_BUILT_EVENT_TYPE_ID)
        total = len(sel_events)
        
        self.lbl_selection_summary.setText(f"{dce_count} DCE's, {design_count} Designs and {asbuilt_count} Asbuilts selected ({total} Total)")

    def set_selected_event_ids(self, selected_events: list):
        self.checked_event_ids = set(selected_events)
        self.refresh_table_view()
        self.on_event_checked()

    def get_selected_events(self) -> list:
        # Return objects based on internal checked set
        return self.get_selected_events_objects()

    def get_selected_events_objects(self) -> list:
        # Return list of Event objects, preserving order of all_events (creation/load order)
        # Note: This ignores visual reordering in the table if filters are active or if table was reordered.
        # To support visual order, we scan the table first for visible checked items, then append hidden checked items?
        # For now, sticking to stable all_events order.
        return [e for e in self.all_events if e.id in self.checked_event_ids]
    
    def get_selected_event_ids(self) -> list:
        return [e.id for e in self.get_selected_events_objects()]

    def select_all(self):
        # Select all VISIBLE events
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked)
            event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
            self.checked_event_ids.add(event.id)
        self.table.blockSignals(False)
        self.on_event_checked()

    def deselect_all(self):
        # Deselect all VISIBLE events
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Unchecked)
            event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
            if event.id in self.checked_event_ids:
                self.checked_event_ids.remove(event.id)
        self.table.blockSignals(False)
        self.on_event_checked()

    def clear_filters(self):
        self.txt_filter_search.clear()
        self.cbo_filter_type.set_all_check_state(QtCore.Qt.Checked)
        self.refresh_table_view()

    def on_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            event = self.table.item(row, 1).data(QtCore.Qt.UserRole)
            if item.checkState() == QtCore.Qt.Checked:
                self.checked_event_ids.add(event.id)
            else:
                 if event.id in self.checked_event_ids:
                     self.checked_event_ids.remove(event.id)
            
            self.update_summary()
            # We do NOT emit event_checked here to prevent spamming during bulk updates? 
            # Or we should? Original code emitted on every check.
            self.event_checked.emit(self.get_selected_event_ids())

    def on_event_checked(self):
        self.update_summary()
        self.event_checked.emit(self.get_selected_event_ids())

    def move_item_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.move_row(row, row - 1)
            self.table.selectRow(row - 1)
            
    def move_item_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self.move_row(row, row + 1)
            self.table.selectRow(row + 1)

    def update_order_buttons(self):
        if not self.allow_reorder: return
        
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.btnUp.setEnabled(False)
            self.btnDown.setEnabled(False)
            return

        row = selected_rows[0].row()
        count = self.table.rowCount()
        
        self.btnUp.setEnabled(row > 0)
        self.btnDown.setEnabled(row < count - 1)

    def move_row(self, old_row, new_row):
        self.table.blockSignals(True)
        items = []
        for col in range(self.table.columnCount()):
             items.append(self.table.takeItem(old_row, col))
        
        self.table.removeRow(old_row)
        self.table.insertRow(new_row)
        
        for col, item in enumerate(items):
             self.table.setItem(new_row, col, item)
             
        self.table.blockSignals(False)
        self.on_event_checked()

    def handle_manual_sort(self, logicalIndex):
        if not self.allow_reorder: return 

        header = self.table.horizontalHeader()
        order = QtCore.Qt.AscendingOrder
        if header.sortIndicatorSection() == logicalIndex and header.sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
            order = QtCore.Qt.DescendingOrder
            
        self.table.blockSignals(True) 
        self.table.sortItems(logicalIndex, order)
        self.table.blockSignals(False)
        
        header.setSortIndicator(logicalIndex, order)
        self.on_event_checked()

    def setupUi(self):
        self.vert_layout = QtWidgets.QVBoxLayout(self)
        self.vert_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Filters ---
        self.horiz_filters = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_filters)

        self.cbo_filter_type = CheckableComboBox()
        self.cbo_filter_type.setPlaceholderText("All Types")
        self.cbo_filter_type.setNoneCheckedText("No Types")
        self.cbo_filter_type.popupClosed.connect(self.refresh_table_view)
        # Fix width to be consistent
        self.cbo_filter_type.setMinimumWidth(200)
        self.horiz_filters.addWidget(self.cbo_filter_type)
        
        self.txt_filter_search = QtWidgets.QLineEdit()
        self.txt_filter_search.setPlaceholderText("Search Events...")
        self.txt_filter_search.textChanged.connect(self.refresh_table_view)
        self.horiz_filters.addWidget(self.txt_filter_search)

        self.btn_clear_filters = QtWidgets.QPushButton()
        self.btn_clear_filters.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/clear_filter'))
        self.btn_clear_filters.setToolTip("Clear Filters")
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        self.horiz_filters.addWidget(self.btn_clear_filters)

        self.lbl_view_count = QtWidgets.QLabel("")
        self.horiz_filters.addWidget(self.lbl_view_count)

        self.horiz_filters.addStretch()

        # --- Table ---
        self.table = ReorderableTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['', 'Name', 'Date', 'Type', 'Description'])
        self.table.verticalHeader().setVisible(False)
        # Single Selection for HIGHLIGHTING
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        if self.allow_reorder:
            self.table.setSortingEnabled(False)
            self.table.horizontalHeader().setSectionsClickable(True)
            self.table.horizontalHeader().sectionClicked.connect(self.handle_manual_sort)
            self.table.orderChanged.connect(self.on_event_checked)
            self.table.itemSelectionChanged.connect(self.update_order_buttons)

        # --- Content Layout ---
        self.content_layout = QtWidgets.QHBoxLayout()

        if self.allow_reorder:
            self.side_btn_layout = QtWidgets.QVBoxLayout()
            self.btnUp = QtWidgets.QPushButton()
            self.btnUp.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/arrow_drop_up'))
            self.btnUp.setToolTip("Move Selection Up")
            self.btnUp.clicked.connect(self.move_item_up)
            self.btnUp.setEnabled(False)

            self.btnDown = QtWidgets.QPushButton()
            self.btnDown.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/arrow_drop_down'))
            self.btnDown.setToolTip("Move Selection Down")
            self.btnDown.clicked.connect(self.move_item_down)
            self.btnDown.setEnabled(False)

            self.side_btn_layout.addWidget(self.btnUp)
            self.side_btn_layout.addWidget(self.btnDown)
            self.side_btn_layout.addStretch()

            self.content_layout.addWidget(self.table)
            self.content_layout.addLayout(self.side_btn_layout)
        else:
            self.content_layout.addWidget(self.table)

        self.vert_layout.addLayout(self.content_layout)

        # --- Bottom Bar ---
        self.horiz_layout = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_layout)

        # Summary Label (Left)
        self.lbl_selection_summary = QtWidgets.QLabel("")
        self.horiz_layout.addWidget(self.lbl_selection_summary)

        self.horiz_layout.addStretch()

        # Buttons (Right)
        self.btnSelectAll = QtWidgets.QPushButton('Select All')
        self.btnSelectAll.clicked.connect(self.select_all)
        self.horiz_layout.addWidget(self.btnSelectAll)

        self.btnDeselectAll = QtWidgets.QPushButton('Select None')
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        self.horiz_layout.addWidget(self.btnDeselectAll)

        self.setLayout(self.vert_layout)
