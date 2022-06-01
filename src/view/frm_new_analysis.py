import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel


from .ui.new_analysis import Ui_Dialog
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.analysis import Analysis, insert_analysis


class FrmNewAnalysis(QDialog, Ui_Dialog):

    def __init__(self, parent, qris_project: Project):

        self.qris_project = qris_project
        self.analysis = None

        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Analysis')
        self.buttonBox.accepted.connect(super().accept)
        self.buttonBox.rejected.connect(super().reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        # Masks
        self.masks = self.qris_project.masks
        self.masks_model = DBItemModel(self.masks)
        self.cboMask.setModel(self.masks_model)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide an analysis name to continue.')
            self.txtName.setFocus()
            return()

        self.analysis = None
        try:
            self.analysis = insert_analysis(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
        except Exception as ex:
            if 'unique' in str(ex).lower():
                QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
            return
