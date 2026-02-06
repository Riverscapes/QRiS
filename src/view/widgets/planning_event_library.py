from PyQt5 import QtWidgets, QtCore, QtGui
from .event_library import EventLibraryWidget, SortableTableWidgetItem
from ...model.db_item import DBItemModel, DBItem
from ...model.event import DCE_EVENT_TYPE_ID

class PlanningEventLibraryWidget(EventLibraryWidget):
    """
    Subclass of EventLibraryWidget that adds a 'Representation' column (ComboBox) 
    in place of the checkbox, and handles 'Select All/None' via representation buttons.
    """

    def __init__(self, parent: QtWidgets.QWidget, qris_project, event_types: list=None):
        # State: map event_id -> representation_id (int)
        # 0 or None means 'Not Selected' / 'None'
        self.event_representations = {} 
        
        super().__init__(parent, qris_project, event_types)

    def setupUi(self):
        super().setupUi()
        
        # Customize Headers
        headers = ['Representation', 'Name', 'Date', 'Type', 'Description']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setColumnWidth(0, 160)
        
        # Load Representation Model
        reps = self.qris_project.lookup_tables.get('lkp_representation', {})
        self.rep_model = DBItemModel(reps, include_none=True)
        # Ensure consistent order (e.g. Existing, Proposed)
        self.rep_model.sort_data_by_key()

        # --- Advanced Filters ToolButton ---
        self.advanced_filter_id = -1
        
        self.btn_advanced = QtWidgets.QToolButton(self)
        self.btn_advanced.setText("Advanced Filters")
        self.btn_advanced.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btn_advanced.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        
        self.menu_advanced = QtWidgets.QMenu(self.btn_advanced)
        self.advanced_filter_group = QtWidgets.QActionGroup(self)
        self.advanced_filter_group.setExclusive(True)

        # 1. Show All Events
        self.act_show_all = self.menu_advanced.addAction("Show All Events")
        self.act_show_all.setCheckable(True)
        self.act_show_all.setData(-1)
        self.act_show_all.toggled.connect(lambda c: self.on_advanced_filter_changed(-1) if c else None)
        self.advanced_filter_group.addAction(self.act_show_all)

        # 2. Show All Representation Types
        self.act_show_reps = self.menu_advanced.addAction("Limit to All Representation Types")
        self.act_show_reps.setCheckable(True)
        self.act_show_reps.setData(-2)
        self.act_show_reps.toggled.connect(lambda c: self.on_advanced_filter_changed(-2) if c else None)
        self.advanced_filter_group.addAction(self.act_show_reps)

        # 3. Limit to No Representation
        self.act_no_rep = self.menu_advanced.addAction("Limit to No Representation")
        self.act_no_rep.setCheckable(True)
        self.act_no_rep.setData(0)
        self.act_no_rep.toggled.connect(lambda c: self.on_advanced_filter_changed(0) if c else None)
        self.advanced_filter_group.addAction(self.act_no_rep)
        
        self.menu_advanced.addSeparator()

        # 4. Dynamic Filters
        for row_idx in range(self.rep_model.rowCount(None)):
            item: DBItem = self.rep_model.data(self.rep_model.index(row_idx), QtCore.Qt.UserRole)
            if item.id == 0: continue
            
            act = self.menu_advanced.addAction(f"Limit to {item.name}")
            act.setCheckable(True)
            act.setData(item.id)
            act.toggled.connect(lambda c, i=item.id: self.on_advanced_filter_changed(i) if c else None)
            self.advanced_filter_group.addAction(act)
            
        self.btn_advanced.setMenu(self.menu_advanced)
        
        # Add to layout (Right side)
        # horiz_filters has [FilterType, Search, Clear, Count, Stretch]
        # We add it after the stretch?
        self.horiz_filters.addWidget(self.btn_advanced) 
        
        # Set Default
        self.act_show_all.setChecked(True)

        # Update Buttons
        # Hide the inherited 'Select All' / 'Select None' buttons instead of deleting them
        # to preserve layout integrity and avoid potential reference issues.
        if hasattr(self, 'btnSelectAll') and self.btnSelectAll is not None:
            self.btnSelectAll.setVisible(False)
        
        if hasattr(self, 'btnDeselectAll') and self.btnDeselectAll is not None:
            self.btnDeselectAll.setVisible(False)
            
        # Check if we already added our custom buttons (to avoid duplication if setupUi recalled)
        if hasattr(self, 'btnSetNone') and self.btnSetNone is not None:
             self.btnSetNone.setVisible(False)
             self.horiz_layout.removeWidget(self.btnSetNone)
             self.btnSetNone.deleteLater()
             self.btnSetNone = None

        # Add "Set visible to:" label
        self.lblSetVisibleTo = QtWidgets.QLabel("Set visible to:") 
        self.horiz_layout.addWidget(self.lblSetVisibleTo)

        # Add "None" button
        self.btnSetNone = QtWidgets.QPushButton('None')
        self.btnSetNone.clicked.connect(lambda checked: self.batch_set_representation(0))
        self.horiz_layout.addWidget(self.btnSetNone)

        # Clear any existing dynamic buttons (if setupUi is recalled)
        # We can't easily track dynamic buttons unless we stored them. 
        # For now, we assume setupUi is called once. 
        
        # Add buttons for each active representation (likely just Existing/Proposed)
        for row_idx in range(self.rep_model.rowCount(None)):
            item: DBItem = self.rep_model.data(self.rep_model.index(row_idx), QtCore.Qt.UserRole)
            if item.id == 0: continue # Skip None
            
            btn = QtWidgets.QPushButton(f'{item.name}')
            btn.clicked.connect(lambda checked, i=item.id: self.batch_set_representation(i))
            self.horiz_layout.addWidget(btn)

    def on_advanced_filter_changed(self, filter_id):
        self.advanced_filter_id = filter_id
        self.refresh_table_view()

    def refresh_table_view(self):
        # Filter Logic (copied/adapted from parent since we need to rebuild the table completely)
        search_text = self.txt_filter_search.text().lower().strip()
        checked_types = self.cbo_filter_type.get_checked_items()
        
        filtered_events = []
        for e in self.all_events:
            # 1. Search Text
            if search_text and search_text not in e.name.lower():
                continue
            # 2. Type Filter (if visible/used)
            if e.event_type.name not in checked_types:
                continue
            
            # 3. Advanced Filter
            current_rep_id = self.event_representations.get(e.id, 0)
            
            if self.advanced_filter_id == -1: # Show All Events
                pass
            elif self.advanced_filter_id == -2: # Show All Representation Types ( != None)
                if current_rep_id == 0: continue
            elif self.advanced_filter_id == 0: # Limit to No Rep ( == 0)
                if current_rep_id != 0: continue
            else: # Specific ID
                if current_rep_id != self.advanced_filter_id: continue

            filtered_events.append(e)

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(filtered_events))
        
        for i, event in enumerate(filtered_events):
            # 0: Representation ComboBox
            # We must create a specific combobox for this cell
            combo = QtWidgets.QComboBox()
            combo.setModel(self.rep_model)
            
            current_rep_id = self.event_representations.get(event.id, 0)
            idx = self.rep_model.getItemIndexById(current_rep_id)
            if idx is not None:
                combo.setCurrentIndex(idx)
            else:
                combo.setCurrentIndex(0)
            
            # Connect signal
            combo.currentIndexChanged.connect(lambda index, e=event: self.on_representation_changed(e, index))
            
            self.table.setCellWidget(i, 0, combo)
            
            # Set a dummy item for potential sorting or data retrieval
            sortItem = QtWidgets.QTableWidgetItem()
            sortItem.setData(QtCore.Qt.UserRole, current_rep_id)
            self.table.setItem(i, 0, sortItem)

            font = QtGui.QFont()
            if current_rep_id != 0:
                font.setBold(True)

            # 1: Name + Icon 
            item = QtWidgets.QTableWidgetItem(event.name)
            item.setData(QtCore.Qt.UserRole, event) 
            icon_alias = self.get_icon_alias(event.event_type.id)
            if icon_alias:
                item.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/{icon_alias}'))
            item.setFont(font)
            self.table.setItem(i, 1, item)
            
            # 2: Date
            date_item = SortableTableWidgetItem(event.date)
            sort_key = (0,0,0)
            if event.start:
                sort_key = (event.start.year or 0, event.start.month or 0, event.start.day or 0)
            date_item.setData(QtCore.Qt.UserRole, sort_key)
            date_item.setFont(font)
            self.table.setItem(i, 2, date_item)

            # 3: Type
            type_item = QtWidgets.QTableWidgetItem(event.event_type.name)
            type_item.setFont(font)
            self.table.setItem(i, 3, type_item)

            # 4: Description
            desc_item = QtWidgets.QTableWidgetItem(event.description or "")
            desc_item.setFont(font)
            self.table.setItem(i, 4, desc_item)
        
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 160) # Keep Rep column wider
        self.table.blockSignals(False)
        
        self.update_summary()

    def on_representation_changed(self, event, index):
        # Retrieve the rep ID from the model using the index
        rep_db_item: DBItem = self.rep_model.data(self.rep_model.index(index), QtCore.Qt.UserRole)
        
        if rep_db_item:
            self.event_representations[event.id] = rep_db_item.id
            
            # Update row font
            # Find the row for this event
            # Since we don't have row index passed here but we need it. 
            # The sender is the combobox. We can find it in the table.
            combo = self.sender()
            if isinstance(combo, QtWidgets.QComboBox):
                # This is O(N) but safer than assuming index alignment if sorting was enabled (it's not currently allowed)
                # Actually, sender() is reliable.
                # Find position in table
                # Easier: just iterate rows or store row in combo property?
                # Actually, refresh_table_view disables sorting so row indices are stable in terms of visual order?
                # But filtering changes Visual rows vs Model rows.
                # Let's find the widget.
                
                # TableWidget provides indexAt(pos) but that requires pos.
                # We can iterate visible rows.
                for row in range(self.table.rowCount()):
                    if self.table.cellWidget(row, 0) == combo:
                        font = QtGui.QFont()
                        if rep_db_item.id != 0:
                            font.setBold(True)
                        
                        for col in range(1, 5):
                            item = self.table.item(row, col)
                            if item:
                                item.setFont(font)
                        break
        
        self.update_summary()

    def batch_set_representation(self, rep_id):
        # Iterate over visible rows and set the combobox
        idx = self.rep_model.getItemIndexById(rep_id)
        if idx is None: return

        # We don't block signals on the table because we want the individual combos to fire their signals
        # Wait, if we setCurrentIndex on 100 items, we get 100 signals.
        # Efficient? Probably fine for <1000 items.
        
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row): continue
            
            combo = self.table.cellWidget(row, 0)
            if isinstance(combo, QtWidgets.QComboBox):
                if combo.currentIndex() != idx:
                    combo.setCurrentIndex(idx)
        
        self.update_summary()

    def update_summary(self):
        # Count selected (non-None) representations
        counts = {}
        total = 0
        
        selected_reps = {e_id: r_id for e_id, r_id in self.event_representations.items() if r_id != 0}
        
        for r_id in selected_reps.values():
            if r_id == 0: continue
            
            # Find name
            idx = self.rep_model.getItemIndexById(r_id)
            if idx is not None:
                item = self.rep_model.data(self.rep_model.index(idx), QtCore.Qt.UserRole)
                name = item.name
                counts[name] = counts.get(name, 0) + 1
        
        parts = [f"{count} {name}" for name, count in counts.items()]
        total = len(selected_reps)
        
        if total == 0:
            summary_text = "No Events"
        else:
            summary_text = ", ".join(parts)
            
        self.lbl_selection_summary.setText(f"{summary_text} Selected ({self.table.rowCount()} Visible)")

    # --- API Compatibility & Accessors ---

    def set_event_representations(self, mapping: dict):
        """
        Set selected events and their representations.
        Dict format: {event_id: representation_id}
        """
        if mapping:
            self.event_representations = {int(k): int(v) for k,v in mapping.items()}
            # If we have representations (existing design/saved state), default to "Show All Representation Types" (-2)
            self.act_show_reps.setChecked(True)
        else:
            self.event_representations = {}
            # If new/empty, default to "Show All Events" (-1)
            self.act_show_all.setChecked(True)
        self.refresh_table_view()

    def set_event_ids(self, mapping: dict):
        # Alias for legacy or consistent naming
        self.set_event_representations(mapping)
        
    def set_selected_event_ids(self, ids: list):
        # If passed a list of IDs, default them to 'Existing' (likely ID 1) if available, else 0
        target_rep = 1
        
        # Try finding 'Existing' explicitly
        idx = self.rep_model.getItemIndexByName('Existing')
        if idx is not None:
             item = self.rep_model.data(self.rep_model.index(idx), QtCore.Qt.UserRole)
             target_rep = item.id
        else:
             # Fallback: check if hardcoded 1 is valid, otherwise grab first available
             if self.rep_model.getItemIndexById(1) is None:
                 if self.rep_model.rowCount(None) > 1:
                     # Index 0 is 'None' (ID 0), so Index 1 is the first real option
                     item = self.rep_model.data(self.rep_model.index(1), QtCore.Qt.UserRole)
                     target_rep = item.id
        
        new_map = {}
        for eid in ids:
            new_map[eid] = target_rep
        self.set_event_representations(new_map)
        
    def get_event_representations(self) -> dict:
        """
        Return dict {event_id: representation_id} for all events where representation is not None (0).
        """
        return {k: v for k, v in self.event_representations.items() if v != 0}

    def get_event_values(self) -> dict:
        # Legacy alias
        return self.get_event_representations()

    def get_selected_event_ids(self) -> list:
        # Compatibility with parent class
        return [k for k, v in self.event_representations.items() if v != 0]
