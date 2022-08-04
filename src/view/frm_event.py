from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox, QLabel
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from ..model.event import Event, insert as insert_event
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project

from .ui.event2 import Ui_event2
from .frm_date_picker import FrmDatePicker

DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmEvent(QDialog, Ui_event2):

    def __init__(self, parent, qris_project: Project, event: Event = None):

        self.qris_project = qris_project
        self.event = event
        self.protocols = []
        self.metadata = None

        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Data Capture Event' if event is None else 'Edit Data Capture Event')
        self.buttonBox.accepted.connect(super(FrmEvent, self).accept)
        self.buttonBox.rejected.connect(super(FrmEvent, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        self.uc_start = FrmDatePicker()
        self.gridLayout.addWidget(self.uc_start, 0, 1)

        self.uc_end = FrmDatePicker()
        self.gridLayout.addWidget(self.uc_end, 1, 1)

        # Protocols
        self.protocol_model = QStandardItemModel()
        for protocol in qris_project.protocols.values():
            if protocol.has_custom_ui == 0:
                item = QStandardItem(protocol.name)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(protocol, Qt.UserRole)
                self.protocol_model.appendRow(item)

                checked_state = Qt.Checked if event is not None and protocol in event.protocols else Qt.Unchecked
                item.setData(QVariant(checked_state), Qt.CheckStateRole)

        self.vwProtocols.setModel(self.protocol_model)
        self.vwProtocols.setModelColumn(1)

        # Basemaps
        self.basemap_model = QStandardItemModel()
        for basemap in qris_project.basemaps.values():
            item = QStandardItem(basemap.name)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(basemap, Qt.UserRole)
            self.basemap_model.appendRow(item)

            checked_state = Qt.Checked if event is not None and basemap in event.basemaps else Qt.Unchecked
            item.setData(QVariant(checked_state), Qt.CheckStateRole)

        self.vwBasemaps.setModel(self.basemap_model)
        self.vwBasemaps.setModelColumn(1)

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.cboPlatform.setModel(self.platform_model)

        if event is not None:
            self.txtName.setText(event.name)
            self.txtDescription.setPlainText(event.description)

            self.uc_start.set_date_spec(event.start)
            self.uc_end.set_date_spec(event.end)

            self.chkAddToMap.setCheckState(Qt.Unchecked)

        self.txtName.setFocus()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Data Capture Event Name', 'You must provide a name for the data capture event to continue.')
            self.txtName.setFocus()
            return

        if len(self.protocols) < 1:
            for row in range(self.protocol_model.rowCount()):
                index = self.protocol_model.index(row, 0)
                check = self.protocol_model.data(index, Qt.CheckStateRole)
                if check == Qt.Checked:
                    for protocol in self.qris_project.protocols.values():
                        if protocol == self.protocol_model.data(index, Qt.UserRole):
                            self.protocols.append(protocol)
                            break

            if len(self.protocols) < 1:
                QMessageBox.warning(self, 'No Protocols Selected', 'You must select at least one protocol to continue.')
                return

        basemaps = []
        for row in range(self.basemap_model.rowCount()):
            index = self.basemap_model.index(row, 0)
            check = self.basemap_model.data(index, Qt.CheckStateRole)
            if check == Qt.Checked:
                for basemap in self.qris_project.basemaps.values():
                    if basemap == self.basemap_model.data(index, Qt.UserRole):
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
                        response = QMessageBox.question(self, 'Possible Data Loss',
                                                        """One or more layers that were part of this data capture event are no longer associated with the event.
                        Continuing might lead to the loss of geospatial data. Do you want to continue?
                        "Click Yes to proceed and delete all data associated with layers that are no longer used by the
                        current data capture event protocols. Click No to stop and avoid any data loss.""")
                        if response == QMessageBox.No:
                            return

            self.event.update(self.txtName.text(), self.txtDescription.toPlainText(), self.protocols, basemaps)

        else:
            try:
                self.event = insert_event(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    self.uc_start.get_date_spec(),
                    self.uc_end.get_date_spec(),
                    '',
                    self.qris_project.lookup_tables['lkp_event_types'][DATA_CAPTURE_EVENT_TYPE_ID],
                    self.cboPlatform.currentData(Qt.UserRole),
                    self.protocols,
                    basemaps,
                    self.metadata
                )

                self.qris_project.events[self.event.id] = self.event
                super().accept()

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A data capture event with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Data Capture Event', str(ex))
