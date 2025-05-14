from PyQt5 import QtWidgets, QtCore

from ...model.db_item import DBItem
from ...model.event import Event
from ...model.project import Project

class EventLibraryWidget(QtWidgets.QWidget):
# Implement a Event Library grid picker, which loads events in event library, exposes their date, and type (columns) allows sorting), and has a checkbox 

    # signal emitted when the user checks or unchecks an event
    event_checked = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, event_types: list=None):
        super().__init__(parent)
        self.qris_project = qris_project
        self.event_types = event_types
        self.setupUi()

        self.load_events()

    def load_events(self):

        # raster_types = self.qris_project.lookup_tables['lkp_raster_types']
        # Load events from the project
        self.table.setRowCount(len(self.qris_project.events))
        event: Event = None
        for i, event in enumerate(self.qris_project.events.values()):
            # Create a checkbox and add it to the cell widget
            checkBox = QtWidgets.QCheckBox()
            self.table.setCellWidget(i, 0, checkBox)
            checkBox.stateChanged.connect(self.on_event_checked)
            
            # Store the entire Event object in the first column using a custom role
            item = QtWidgets.QTableWidgetItem(event.name)
            item.setData(QtCore.Qt.UserRole, event)
            self.table.setItem(i, 1, item)
            
            # Set other event properties in the table
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(event.date))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(event.event_type.name))
        
        # resize column 0 to fit the checkboxes
        self.table.setColumnWidth(0, 30)
        self.table.resizeColumnsToContents()

    def set_selected_event_ids(self, selected_events: list):
        # set a list of selected events by their ids

        for i in range(self.table.rowCount()):
            event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
            if event.id in selected_events:
                self.table.cellWidget(i, 0).setChecked(True)

    def get_selected_events(self) -> list:
        # Return the selected events by object

        selected_events = []
        for i in range(self.table.rowCount()):
            if self.table.cellWidget(i, 0).isChecked():
                event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_events.append(event)
        return selected_events
    
    def get_selected_event_ids(self) -> list:
        # Return the selected events by id

        selected_events = []
        for i in range(self.table.rowCount()):
            if self.table.cellWidget(i, 0).isChecked():
                event: Event = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_events.append(event.id)
        return selected_events

    def select_all(self):
        for i in range(self.table.rowCount()):
            self.table.cellWidget(i, 0).setChecked(True)

    def deselect_all(self):
        for i in range(self.table.rowCount()):
            self.table.cellWidget(i, 0).setChecked(False)

    # emit the selected event ids when the user checks or unchecks an event
    def on_event_checked(self, state):
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
        self.table.setSortingEnabled(True)
        self.vert_layout.addWidget(self.table)

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