import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox, QLabel, QComboBox
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
from .frm_event import FrmEvent
from .frm_date_picker import FrmDatePicker

DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmDesign(FrmEvent):

    def __init__(self, parent, qris_project: Project, event=None):
        super().__init__(parent, qris_project, event)

        self.setWindowTitle('Create New Design' if event is None else 'Edit Design')

        self.lblStatus = QLabel('Design Status', self)
        self.gridLayout.addWidget(self.lblStatus, 4, 0)

        self.cboStatus = QComboBox(self)
        self.status_model = DBItemModel(qris_project.lookup_tables['lkp_design_status'])
        self.cboStatus.setModel(self.status_model)
        self.gridLayout.addWidget(self.cboStatus, 4, 1)

        self.vwProtocols.setVisible(False)
        self.lblProtocols.setVisible(False)

    def accept(self):

        self.metadata = {'statusId': self.cboStatus.currentData(Qt.UserRole).id}
        self.protocols = [self.qris_project.protocols[3]]

        super().accept()

    #     if len(self.txtName.text()) < 1:
    #         QMessageBox.warning(self, 'Missing Data Capture Event Name', 'You must provide a name for the data capture event to continue.')
    #         self.txtName.setFocus()
    #         return

    #     protocols = []
    #     for row in range(self.protocol_model.rowCount()):
    #         index = self.protocol_model.index(row, 0)
    #         check = self.protocol_model.data(index, Qt.CheckStateRole)
    #         if check == Qt.Checked:
    #             for protocol in self.qris_project.protocols.values():
    #                 if protocol == self.protocol_model.data(index, Qt.UserRole):
    #                     protocols.append(protocol)
    #                     break

    #     if len(protocols) < 1:
    #         QMessageBox.warning(self, 'No Protocols Selected', 'You must select at least one protocol to continue.')
    #         return

    #     basemaps = []
    #     # for row in range(self.bases_model.rowCount()):
    #     #     index = self.bases_model.index(row, 0)
    #     #     check = self.bases_model.data(index, Qt.CheckStateRole)
    #     #     if check == Qt.Checked:
    #     #         for basemap in self.qris_project.basemaps.values():
    #     #             if basemap.name == self.bases_model.data(index, Qt.DisplayRole):
    #     #                 basemaps.append(basemap)

    #     try:
    #         self.event = insert_event(
    #             self.qris_project.project_file,
    #             self.txtName.text(),
    #             self.txtDescription.toPlainText(),
    #             self.uc_start.get_date_spec(),
    #             self.uc_end.get_date_spec(),
    #             '',
    #             self.qris_project.lookup_tables['lkp_event_types'][DATA_CAPTURE_EVENT_TYPE_ID],
    #             self.cboPlatform.currentData(Qt.UserRole),
    #             protocols,
    #             basemaps,
    #             None
    #         )

    #         self.qris_project.events[self.event.id] = self.event
    #         super().accept()

    #     except Exception as ex:
    #         if 'unique' in str(ex).lower():
    #             QMessageBox.warning(self, 'Duplicate Name', "A data capture event with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
    #             self.txtName.setFocus()
    #         else:
    #             QMessageBox.warning(self, 'Error Saving Data Capture Event', str(ex))
