from PyQt5 import QtWidgets, QtCore

from ...model.db_item import DBItem
from ...model.event import Event
from ...model.project import Project

class EventLibraryWidget(QtWidgets.QWidget):
# Implement a Event Library grid picker, which loads events in event library, exposes their date, and type (columns) allows sorting), and has a checkbox 

    # signal emitted when the user checks or unchecks an event
    event_checked = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, event_types: list=None, allow_reorder: bool=False):
        super().__init__(parent)
        self.qris_project = qris_project
        self.event_types = event_types
        self.allow_reorder = allow_reorder
        self.setupUi()

        self.load_events()

    def load_events(self, events: list = None):

        # raster_types = self.qris_project.lookup_tables['lkp_raster_types']
        # Load events from the project
        
        self.table.blockSignals(True)

        if events is None:
            events = list(self.qris_project.events.values())

        if self.event_types is not None:
            events = [e for e in events if e.event_type.id in self.event_types]

        self.table.setRowCount(len(events))
        event: Event = None
        for i, event in enumerate(events):
            # Create a checkbox and add it to the first column
            checkItem = QtWidgets.QTableWidgetItem()
            checkItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            if self.allow_reorder:
                checkItem.setFlags(checkItem.flags() | QtCore.Qt.ItemIsDragEnabled)
            checkItem.setCheckState(QtCore.Qt.Unchecked)
            self.table.setItem(i, 0, checkItem)
            
            # Store the entire Event object in the first column using a custom role
            item = QtWidgets.QTableWidgetItem(event.name)
            item.setData(QtCore.Qt.UserRole, event)
            if self.allow_reorder:
                item.setFlags(item.flags() | QtCore.Qt.ItemIsDragEnabled)

            self.table.setItem(i, 1, item)
            
            # Set other event properties in the table
            date_item = QtWidgets.QTableWidgetItem(event.date)
            if self.allow_reorder:
                date_item.setFlags(date_item.flags() | QtCore.Qt.ItemIsDragEnabled)
            self.table.setItem(i, 2, date_item)

            type_item = QtWidgets.QTableWidgetItem(event.event_type.name)
            if self.allow_reorder:
                type_item.setFlags(type_item.flags() | QtCore.Qt.ItemIsDragEnabled)
            self.table.setItem(i, 3, type_item)
        
        # resize column 0 to fit the checkboxes
        self.table.setColumnWidth(0, 30)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def set_selected_event_ids(self, selected_events: list):
        # set a list of selected events by their ids
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
            if event.id in selected_events:
                self.table.item(i, 0).setCheckState(QtCore.Qt.Checked)
            else:
                self.table.item(i, 0).setCheckState(QtCore.Qt.Unchecked)
        self.table.blockSignals(False)
        self.on_event_checked()

    def get_selected_events(self) -> list:
        # Return the selected events by object

        selected_events = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == QtCore.Qt.Checked:
                event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_events.append(event)
        return selected_events
    
    def get_selected_event_ids(self) -> list:
        # Return the selected events by id

        selected_events = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == QtCore.Qt.Checked:
                event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_events.append(event.id)
        return selected_events

    def select_all(self):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked)
        self.table.blockSignals(False)
        self.on_event_checked()

    def deselect_all(self):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Unchecked)
        self.table.blockSignals(False)
        self.on_event_checked()

    # emit the selected event ids when the user checks or unchecks an event
    def on_item_changed(self, item):
        if item.column() == 0:
            self.on_event_checked()

    def move_item_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.move_row(row, row - 1)
            self.table.selectRow(row - 1)
            
    def move_item_down(self):
        row = self.table.currentRow()
        if row < self.table.rowCount() - 1:
            self.move_row(row, row + 1)
            self.table.selectRow(row + 1)

    def move_row(self, old_row, new_row):
        self.table.blockSignals(True)
        items = []
        for col in range(self.table.columnCount()):
             items.append(self.table.takeItem(old_row, col))
        
        self.table.removeRow(old_row)
        self.table.insertRow(new_row)
        
        for col, item in enumerate(items):
             self.table.setItem(new_row, col, item)
             
        # Restore widget in first column logic? 
        # We switched to using straight QTableWidgetItem with flags, so no setCellWidget.
        # This simplifies moving significantly.
        
        self.table.blockSignals(False)
        self.on_event_checked()

    def on_event_checked(self):
        selected_events = self.get_selected_event_ids()
        self.event_checked.emit(selected_events)

    def setupUi(self):

        self.vert_layout = QtWidgets.QVBoxLayout(self)
        self.vert_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['', 'Name', 'Date', 'Type'])
        # self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        if self.allow_reorder:
            self.table.setDragEnabled(True)
            self.table.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.table.setSortingEnabled(False)
        else:
            self.table.setSortingEnabled(True)
        
        self.table.itemChanged.connect(self.on_item_changed)

        # Container for table and side buttons
        self.content_layout = QtWidgets.QHBoxLayout()
        self.content_layout.addWidget(self.table)

        if self.allow_reorder:
            self.side_btn_layout = QtWidgets.QVBoxLayout()
            
            self.btnUp = QtWidgets.QPushButton()
            self.btnUp.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp))
            self.btnUp.setToolTip("Move Selection Up")
            self.btnUp.clicked.connect(self.move_item_up)
            
            self.btnDown = QtWidgets.QPushButton()
            self.btnDown.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
            self.btnDown.setToolTip("Move Selection Down")
            self.btnDown.clicked.connect(self.move_item_down)

            self.side_btn_layout.addWidget(self.btnUp)
            self.side_btn_layout.addWidget(self.btnDown)
            self.side_btn_layout.addStretch()
            
            self.content_layout.addLayout(self.side_btn_layout)

        self.vert_layout.addLayout(self.content_layout)

        self.horiz_layout = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_layout)

        self.horiz_layout.addStretch()

        self.btnSelectAll = QtWidgets.QPushButton('Select All')
        self.btnSelectAll.clicked.connect(self.select_all)
        self.horiz_layout.addWidget(self.btnSelectAll)

        self.btnDeselectAll = QtWidgets.QPushButton('Select None')
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        self.horiz_layout.addWidget(self.btnDeselectAll)


        self.setLayout(self.vert_layout)