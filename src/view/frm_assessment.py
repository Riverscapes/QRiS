import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table

from .ui.assessment import Ui_Assessment


class CheckBoxListTableModel(QSqlTableModel):
    def __init__(self, *args, **kwargs):

        QSqlTableModel.__init__(self, *args, **kwargs)
        self.checkeable_data = {}

    def flags(self, index):
        fl = QSqlTableModel.flags(self, index)
        if index.column() == 1:
            fl |= Qt.ItemIsUserCheckable
        return fl

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.CheckStateRole and (
            self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
        ):
            if index.row() not in self.checkeable_data.keys():
                self.setData(index, Qt.Unchecked, Qt.CheckStateRole)
            return self.checkeable_data[index.row()]
        else:
            return QSqlTableModel.data(self, index, role)

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and (
            self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
        ):
            self.checkeable_data[index.row()] = value
            self.dataChanged.emit(index, index, (role,))
            return True
        return QSqlTableModel.setData(self, index, value, role)


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

        db = QSqlDatabase('QSQLITE')
        db.setDatabaseName(qris_project.project_file)
        if not db.open():
            print('uh oh')

        self.model = CheckBoxListTableModel(self, db=db)
        self.model.setTable('methods')
        self.model.select()

        # for row in range(self.model.rowCount()):
        #     index = self.model.index(row, 0)
        #     self.model.setData(index, Qt.Checked, Qt.CheckStateRole)

        # item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        self.vwMethods.setModel(self.model)
        self.vwMethods.setModelColumn(1)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Assessment Name', 'You must provide an assessment name to continue.')
            self.txtName.setFocus()
            return()

        methods = []
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            check = self.model.data(index, Qt.CheckStateRole)
            if check is not None:
                methods.append(self.model.data(index, Qt.DisplayRole))

        if len(methods) < 1:
            QMessageBox.warning(self, 'No Methods Selected', 'You must select at least one method to continue.')
            self.txtProjectName.setFocus()
            return()

        conn = sqlite3.connect(self.qris_project.project.file)

        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO assessments (name, description) VALUES (?, ?)', [self.txtName.text(), self.txtDescription.text()])
            self.assessment_id = curs.lastrowid

            assessment_methods = [(self.assessment_id, method_id) for method_id in methods]
            curs.executemany('INSERT INTO assessment_methods (assessment_id, method_id) VALUES (?, ?)', assessment_methods)
            conn.commit()
            super(FrmAssessment, self).accept()

        except Exception as ex:
            conn.rollback()
            QMessageBox.warning(self, 'Error Saving Assessment', ex)
