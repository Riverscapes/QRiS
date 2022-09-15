
from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.event import Event, insert as insert_event
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project

from .frm_date_picker import FrmDatePicker

from datetime import date, datetime
from .utilities import validate_name, add_standard_form_buttons


DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmEvent(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, event_type_id: int = DATA_CAPTURE_EVENT_TYPE_ID, event: Event = None):

        self.qris_project = qris_project
        self.event = event
        self.protocols = []
        self.metadata = None
        self.event_type_id = event_type_id

        super().__init__(parent)
        self.setupUi()
        self.setWindowTitle('Create New Data Capture Event' if event is None else 'Edit Data Capture Event')
        self.buttonBox.accepted.connect(super(FrmEvent, self).accept)
        self.buttonBox.rejected.connect(super(FrmEvent, self).reject)

        # Protocols
        self.protocol_model = QtGui.QStandardItemModel()
        for protocol in qris_project.protocols.values():
            if protocol.has_custom_ui == 0:
                item = QtGui.QStandardItem(protocol.name)
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                item.setData(protocol, QtCore.Qt.UserRole)
                self.protocol_model.appendRow(item)

                checked_state = QtCore.Qt.Checked if event is not None and protocol in event.protocols else QtCore.Qt.Unchecked
                item.setData(QtCore.QVariant(checked_state), QtCore.Qt.CheckStateRole)

        self.vwProtocols.setModel(self.protocol_model)
        self.vwProtocols.setModelColumn(1)

        # Basemaps
        self.basemap_model = QtGui.QStandardItemModel()
        for basemap in qris_project.basemaps().values():
            item = QtGui.QStandardItem(basemap.name)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setData(basemap, QtCore.Qt.UserRole)
            self.basemap_model.appendRow(item)

            checked_state = QtCore.Qt.Checked if event is not None and basemap in event.basemaps else QtCore.Qt.Unchecked
            item.setData(QtCore.QVariant(checked_state), QtCore.Qt.CheckStateRole)

        self.vwBasemaps.setModel(self.basemap_model)
        self.vwBasemaps.setModelColumn(1)

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.cboPlatform.setModel(self.platform_model)

        if event is not None:
            self.txtName.setText(event.name)
            self.txtDescription.setPlainText(event.description)
            self.cboPlatform.setCurrentIndex(event.platform.id - 1)

            self.uc_start.set_date_spec(event.start)
            self.uc_end.set_date_spec(event.end)

            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.txtName.setFocus()

    def accept(self):
        start_date_valid, start_date_error_msg = self.uc_start.validate()
        if not start_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Start Date', start_date_error_msg)
            self.uc_start.setFocus()
            return

        end_date_valid, end_date_error_msg = self.uc_end.validate()
        if not end_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid End Date', end_date_error_msg)
            self.uc_end.setFocus()
            return

        start_date = self.uc_start.get_date_spec()
        end_date = self.uc_end.get_date_spec()

        date_order_valid = check_if_date_order_valid(start_date, end_date)
        if not date_order_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Date Order', "")
            self.uc_end.setFocus()
            return

        if not validate_name(self, self.txtName):
            return

        if len(self.protocols) < 1:
            for row in range(self.protocol_model.rowCount()):
                index = self.protocol_model.index(row, 0)
                check = self.protocol_model.data(index, QtCore.Qt.CheckStateRole)
                if check == QtCore.Qt.Checked:
                    for protocol in self.qris_project.protocols.values():
                        if protocol == self.protocol_model.data(index, QtCore.Qt.UserRole):
                            self.protocols.append(protocol)
                            break

            if len(self.protocols) < 1:
                QtWidgets.QMessageBox.warning(self, 'No Protocols Selected', 'You must select at least one protocol to continue.')
                return

        basemaps = []
        for row in range(self.basemap_model.rowCount()):
            index = self.basemap_model.index(row, 0)
            check = self.basemap_model.data(index, QtCore.Qt.CheckStateRole)
            if check == QtCore.Qt.Checked:
                for basemap in self.qris_project.basemaps().values():
                    if basemap == self.basemap_model.data(index, QtCore.Qt.UserRole):
                        basemaps.append(basemap)
                        break

        if self.event is not None:
            # Check if any GIS data might be lost
            for originial_protocol in self.event.protocols:
                for original_layer in originial_protocol.layers:
                    existing_layer_in_use = False
                    for new_protocol in self.protocols:
                        for new_layer in new_protocol.layers:
                            if original_layer == new_layer:
                                existing_layer_in_use = True

                    if existing_layer_in_use is False:
                        response = QtWidgets.QMessageBox.question(self, 'Possible Data Loss',
                                                                  """One or more layers that were part of this data capture event are no longer associated with the event.
                        Continuing might lead to the loss of geospatial data. Do you want to continue?
                        "Click Yes to proceed and delete all data associated with layers that are no longer used by the
                        current data capture event protocols. Click No to stop and avoid any data loss.""")
                        if response == QtWidgets.QMessageBox.No:
                            return

            self.event.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), self.protocols, basemaps, start_date, end_date, self.cboPlatform.currentData(QtCore.Qt.UserRole), self.metadata)
            super().accept()
        else:
            try:
                self.event = insert_event(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    self.uc_start.get_date_spec(),
                    self.uc_end.get_date_spec(),
                    '',
                    self.qris_project.lookup_tables['lkp_event_types'][self.event_type_id],
                    self.cboPlatform.currentData(QtCore.Qt.UserRole),
                    self.protocols,
                    basemaps,
                    self.metadata
                )

                self.qris_project.events[self.event.id] = self.event
                super().accept()

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A data capture event with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Data Capture Event', str(ex))

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(500, 400)

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.tabGridWidget = QtWidgets.QWidget()
        self.tabGrid = QtWidgets.QGridLayout(self.tabGridWidget)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)
        self.tab.addTab(self.tabGridWidget, 'Basic Properties')

        self.lblStartDate = QtWidgets.QLabel()
        self.lblStartDate.setText('Start Date')
        self.tabGrid.addWidget(self.lblStartDate, 0, 0, 1, 1)

        self.uc_start = FrmDatePicker()
        self.tabGrid.addWidget(self.uc_start, 0, 1, 1, 1)

        self.lblEndDate = QtWidgets.QLabel()
        self.lblEndDate.setText('End Date')
        self.tabGrid.addWidget(self.lblEndDate, 1, 0, 1, 1)

        self.uc_end = FrmDatePicker()
        self.tabGrid.addWidget(self.uc_end, 1, 1, 1, 1)

        self.lblPlatform = QtWidgets.QLabel()
        self.lblPlatform.setText('Platform')
        self.tabGrid.addWidget(self.lblPlatform, 2, 0, 1, 1)

        self.cboPlatform = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboPlatform, 2, 1, 1, 1)

        self.lblProtocols = QtWidgets.QLabel()
        self.lblProtocols.setText('Protocols')
        self.tabGrid.addWidget(self.lblProtocols, 3, 0, 1, 1)

        self.vwProtocols = QtWidgets.QListView()
        self.tabGrid.addWidget(self.vwProtocols)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.vert.addWidget(self.chkAddToMap)

        # Basemaps
        self.vwBasemaps = QtWidgets.QListView()
        self.tab.addTab(self.vwBasemaps, 'Basemaps')

        # Description
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        self.vert.addLayout(add_standard_form_buttons(self, 'events'))


def check_if_date_order_valid(start_date: DateSpec, end_date: DateSpec):
    if start_date.year is None or end_date.month is None:
        return True
    elif start_date.month is None or end_date.month is None:
        if start_date.year <= end_date.year:
            return True
        else:
            return False
    elif start_date.day is None or end_date.day is None:
        start_dt = datetime(start_date.year, start_date.month, 1)
        end_dt = datetime(end_date.year, end_date.month, 1)
    else:
        start_dt = datetime(start_date.year, start_date.month, start_date.day)
        end_dt = datetime(end_date.year, end_date.month, end_date.day)

    if start_dt > end_dt:
        return False
    else:
        return True
