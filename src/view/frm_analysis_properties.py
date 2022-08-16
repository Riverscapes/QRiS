import os

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from .ui.analysis_properties import Ui_AnalysisProperties
from ..model.analysis import Analysis
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap, insert_basemap
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project


class FrmAnalysisProperties(QDialog, Ui_AnalysisProperties):

    def __init__(self, parent, project: Project, analysis: Analysis = None):

        self.project = project
        self.analysis = analysis

        super(FrmAnalysisProperties, self).__init__(parent)
        self.setupUi(self)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Analysis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        mask = self.cboMask.currentData(Qt.UserRole)
        if mask is None:
            QMessageBox.warning(self, 'Missing Mask', 'You must select a mask to continue.')
            self.txtName.setFocus()
            return()

        super(FrmAnalysisProperties, self).accept()
