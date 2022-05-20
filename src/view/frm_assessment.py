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

from .ui.assessment import Ui_Assessment


# class CheckBoxListTableModel(QSqlTableModel):
#     def __init__(self, *args, **kwargs):

#         QSqlTableModel.__init__(self, *args, **kwargs)
#         self.checkeable_data = {}

#     def flags(self, index):
#         fl = QSqlTableModel.flags(self, index)
#         if index.column() == 1:
#             fl |= Qt.ItemIsUserCheckable
#         return fl

#     def data(self, index, role=Qt.DisplayRole):
#         if role == Qt.CheckStateRole and (
#             self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
#         ):
#             if index.row() not in self.checkeable_data.keys():
#                 self.setData(index, Qt.Unchecked, Qt.CheckStateRole)
#             return self.checkeable_data[index.row()]
#         else:
#             return QSqlTableModel.data(self, index, role)

#     def setData(self, index, value, role=Qt.EditRole):
#         if role == Qt.CheckStateRole and (
#             self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
#         ):
#             self.checkeable_data[index.row()] = value
#             self.dataChanged.emit(index, index, (role,))
#             return True
#         return QSqlTableModel.setData(self, index, value, role)


# class TableModel(QtCore.QAbstractTableModel):
#     def __init__(self, data):
#         super().__init__()
#         self._data = data

#     def data(self, index, role):
#         if role == Qt.DisplayRole:
#             # See below for the nested-list data structure. # .row() indexes into the outer list,
#             # .column() indexes into the sub-list
#             return self._data[index.row()][index.column()]

#     def rowCount(self, index):
#         # The length of the outer list.
#         return len(self._data)

#     def columnCount(self, index):
#         # The following takes the first sub-list, and returns
#         # the length (only works if all rows are an equal length)
#         return len(self._data[0])


class FrmAssessment(QDialog, Ui_Assessment):

    def __init__(self, parent, qris_project, assessment=None):

        self.qris_project = qris_project
        self.assessment_id = None

        super(FrmAssessment, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Assessment' if assessment is None else 'Edit Assessment Properties')
        self.buttonBox.accepted.connect(super(FrmAssessment, self).accept)
        self.buttonBox.rejected.connect(super(FrmAssessment, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        # Methods
        self.methods_model = QStandardItemModel()
        conn = sqlite3.connect(qris_project.project_file)
        curs = conn.cursor()
        curs.execute('SELECT fid, name FROM methods ORDER BY name')
        for row in curs.fetchall():
            item = QStandardItem(row[1])
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
            self.methods_model.appendRow(item)

        self.vwMethods.setModel(self.methods_model)
        self.vwMethods.setModelColumn(1)

        # Bases
        self.bases_model = QStandardItemModel()
        conn = sqlite3.connect(qris_project.project_file)
        curs = conn.cursor()
        curs.execute('SELECT fid, name FROM bases ORDER BY name')
        for row in curs.fetchall():
            item = QStandardItem(row[1])
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
            self.bases_model.appendRow(item)

        self.vwBasis.setModel(self.bases_model)
        self.vwBasis.setModelColumn(1)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Assessment Name', 'You must provide an assessment name to continue.')
            self.txtName.setFocus()
            return()

        method_names = []
        for row in range(self.methods_model.rowCount()):
            index = self.methods_model.index(row, 0)
            check = self.methods_model.data(index, Qt.CheckStateRole)
            if check == Qt.Checked:
                method_names.append(self.methods_model.data(index, Qt.DisplayRole))

        if len(method_names) < 1:
            QMessageBox.warning(self, 'No Methods Selected', 'You must select at least one method to continue.')
            self.txtProjectName.setFocus()
            return()

        basis_names = []
        for row in range(self.bases_model.rowCount()):
            index = self.bases_model.index(row, 0)
            check = self.bases_model.data(index, Qt.CheckStateRole)
            if check == Qt.Checked:
                basis_names.append(self.bases_model.data(index, Qt.DisplayRole))

        try:
            self.assessment = self.qris_project.add_assessment(self.txtName.text(), self.txtDescription.toPlainText(), method_names, basis_names)
            super().accept()

        except Exception as ex:
            if 'unique' in str(ex).lower():
                QMessageBox.warning(self, 'Assessment Already Exists', "An assessment with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QMessageBox.warning(self, 'Error Saving Assessment', str(ex))
