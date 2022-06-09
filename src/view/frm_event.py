import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox, QLabel
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table

from ..model.event import insert as insert_event
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project

from .ui.event2 import Ui_event2
from .frm_date_picker import FrmDatePicker

DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmEvent(QDialog, Ui_event2):

    def __init__(self, parent, qris_project: Project, event=None):

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

        # Methods
        self.protocol_model = QStandardItemModel()
        for protocol in qris_project.protocols.values():
            if protocol.has_custom_ui is False:
                item = QStandardItem(protocol.name)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
                item.setData(protocol, Qt.UserRole)
                self.protocol_model.appendRow(item)

        self.vwProtocols.setModel(self.protocol_model)
        self.vwProtocols.setModelColumn(1)

        # Basemaps
        self.basemaps_model = DBItemModel(qris_project.basemaps)
        self.vwBasemaps.setModel(self.basemaps_model)

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.cboPlatform.setModel(self.platform_model)

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
        # for row in range(self.bases_model.rowCount()):
        #     index = self.bases_model.index(row, 0)
        #     check = self.bases_model.data(index, Qt.CheckStateRole)
        #     if check == Qt.Checked:
        #         for basemap in self.qris_project.basemaps.values():
        #             if basemap.name == self.bases_model.data(index, Qt.DisplayRole):
        #                 basemaps.append(basemap)

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
