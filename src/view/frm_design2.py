from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox, QLabel, QComboBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project

from .frm_event import FrmEvent

DESIGN_EVENT_TYPE_ID = 2


class FrmDesign(FrmEvent):

    def __init__(self, parent, qris_project: Project, event=None):
        super().__init__(parent, qris_project, DESIGN_EVENT_TYPE_ID, event)

        self.setWindowTitle('Create New Design' if event is None else 'Edit Design')

        self.lblStatus = QLabel('Design Status', self)
        self.tabGrid.addWidget(self.lblStatus, 4, 0)

        statuses = qris_project.lookup_tables['lkp_design_status']
        self.cboStatus = QComboBox(self)
        self.status_model = DBItemModel(statuses)
        self.cboStatus.setModel(self.status_model)
        self.tabGrid.addWidget(self.cboStatus, 4, 1)

        self.vwProtocols.setVisible(False)
        self.lblProtocols.setVisible(False)

        if event is not None:
            self.chkAddToMap.setVisible(False)

            status_id = event.metadata['statusId']
            status_index = self.status_model.getItemIndexById(status_id)
            self.cboStatus.setCurrentIndex(status_index)

    def accept(self):

        self.metadata = {'statusId': self.cboStatus.currentData(Qt.UserRole).id}
        self.protocols = [self.qris_project.protocols[3]]

        super().accept()
