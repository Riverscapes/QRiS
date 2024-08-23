from PyQt5 import QtWidgets, QtCore

from ...model.db_item import DBItem, DBItemModel
from ...model.event import Event
from ...model.project import Project

from ...view.frm_event_picker import FrmEventPicker


class PlanningEventLibraryWidget(QtWidgets.QWidget):
# Implement a Event Library grid picker, which loads events in event library, exposes their date, and type (columns) allows sorting), and has a checkbox 

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, event_types: list = None):
        super().__init__(parent)
        self.qris_project = qris_project
        self.event_types = event_types

        self.setupUi()


    def load_events(self, events):

        # Load events from the project
        event: Event = None
        if self.event_types is not None:
            events = [event for event in events if event.event_type.id in self.event_types]
        self.table.setRowCount(len(events))
        for i, event in enumerate(events):
            
            # Store the entire Event object in the first column using a custom role
            item = QtWidgets.QTableWidgetItem(event.name)
            item.setData(QtCore.Qt.UserRole, event)
            self.table.setItem(i, 0, item)
            
            # Set other event properties in the table
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(event.date))

            # Create a checkbox and add it to the cell widget
            self.table.setCellWidget(i, 2, QtWidgets.QComboBox())
            representation_model = DBItemModel(self.qris_project.lookup_tables['lkp_representation'], include_none=True)
            representation_model._data.sort(key=lambda a: a[0])
            self.table.cellWidget(i, 2).setModel(representation_model)
            self.table.cellWidget(i, 2).setCurrentIndex(0)
        
        self.table.resizeColumnsToContents()

    def set_event_ids(self, events: dict):
        # set a list of selected events by their ids

        for i in range(self.table.rowCount()):
            event: Event = self.table.item(i, 0).data(QtCore.Qt.UserRole)
            value = events.get(event.id, None)
            # get the combobox index
            self.table.cellWidget(i, 2).setCurrentIndex(value)

    def get_event_values(self) -> dict:
        # Return the events by value

        events = {}
        for i in range(self.table.rowCount()):
            # get the combobox value
            output: DBItem = self.table.cellWidget(i, 2).currentData()
            event: Event = self.table.item(i, 0).data(QtCore.Qt.UserRole)
            events[event.id] = output.id
        return events

    def add_event(self):
        
        frm = FrmEventPicker(self, self.qris_project, 1)
        if frm.exec_():
            event = frm.qris_event
            # make sure the event is not already in the list
            for i in range(self.table.rowCount()):
                if self.table.item(i, 0).data(QtCore.Qt.UserRole).id == event.id:
                    return

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(event.name))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(event.date))
            self.table.setCellWidget(row, 2, QtWidgets.QComboBox())
            representation_model = DBItemModel(self.qris_project.lookup_tables['lkp_representation'], include_none=True)
            representation_model._data.sort(key=lambda a: a[0])
            self.table.cellWidget(row, 2).setModel(representation_model)
            self.table.cellWidget(row, 2).setCurrentIndex(0)
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, event)
            self.table.resizeColumnsToContents()

    def remove_event(self):
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).isSelected():
                self.table.removeRow(i)
                break

    def set_all_to_none(self):
        for i in range(self.table.rowCount()):
            self.table.cellWidget(i, 2).setCurrentIndex(0)

    def setupUi(self):

        self.vert_layout = QtWidgets.QVBoxLayout(self)

        self.horiz_table_layout = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_table_layout)

        self.vert_buttons_layout = QtWidgets.QVBoxLayout()
        self.horiz_table_layout.addLayout(self.vert_buttons_layout)

        self.btn_add = QtWidgets.QPushButton('Add')
        self.btn_add.clicked.connect(self.add_event)
        self.vert_buttons_layout.addWidget(self.btn_add)

        self.btn_remove = QtWidgets.QPushButton('Remove')
        self.btn_remove.clicked.connect(self.remove_event)
        self.vert_buttons_layout.addWidget(self.btn_remove)

        self.vert_buttons_layout.addStretch()

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Name', 'Date', 'Representation'])
        # self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.horiz_table_layout.addWidget(self.table)

        self.horiz_layout = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_layout)

        self.horiz_layout.addStretch()

        self.btnDeselectAll = QtWidgets.QPushButton('Set all to None')
        self.btnDeselectAll.clicked.connect(self.set_all_to_none)
        self.horiz_layout.addWidget(self.btnDeselectAll)


        self.setLayout(self.vert_layout)