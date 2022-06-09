import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table
from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayer

from .ui.design import Ui_Design
from ..model.design import Design
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project

from ..model.mask import load_masks, Mask

from ..processing_provider.feature_class_functions import copy_raster_to_project


class FrmDesign(QDialog, Ui_Design):

    def __init__(self, parent, qris_project: Project, design: Design = None):

        self.qris_project = qris_project
        self.design = design

        super(FrmDesign, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Design' if self.design is None else 'Edit Design Properties')
        self.buttonBox.accepted.connect(super(FrmDesign, self).accept)
        self.buttonBox.rejected.connect(super(FrmDesign, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        # self.txtName.textChanged.connect(self.on_name_changed)

        # Assessments
        self.assessments = self.qris_project.events
        assessment_index = None

        if isinstance(design, Design):
            self.txtName.setText(design.name)
            self.txtName.selectAll()
            self.txtDescription.setText(design.description)
            assessment_index = self.ass_model.getItemIndex(design.assessement)
        else:
            self.assessments[0] = DBItem('None', 0, 'Create New Assessment (Epoch) For This Design')

        self.ass_model = DBItemModel(self.assessments)
        self.cboAssessment.setModel(self.ass_model)

        if assessment_index is not None:
            self.cboAssessment.setCurrentIndex(assessment_index)
