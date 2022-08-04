from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox, QLabel, QComboBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project

from .frm_event import FrmEvent

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
