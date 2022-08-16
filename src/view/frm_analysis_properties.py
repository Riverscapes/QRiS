import os

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from .ui.analysis_properties import Ui_AnalysisProperties
from ..model.analysis import Analysis, insert_analysis
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap, insert_basemap
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import REGULAR_MASK_TYPE_ID


class FrmAnalysisProperties(QDialog, Ui_AnalysisProperties):

    def __init__(self, parent, project: Project, analysis: Analysis = None):

        self.project = project
        self.analysis = analysis

        super(FrmAnalysisProperties, self).__init__(parent)
        self.setupUi(self)

        # Masks (filtered to just regular masks )
        self.masks = {id: mask for id, mask in project.masks.items() if mask.mask_type.id == REGULAR_MASK_TYPE_ID}
        self.masks_model = DBItemModel(self.masks)
        self.cboMask.setModel(self.masks_model)

        # Basemaps
        self.basemaps_model = DBItemModel(project.basemaps)
        self.cboBasemap.setModel(self.basemaps_model)

        if analysis is not None:
            self.txtName.setText(analysis.name)
            self.txtDescription.setPlainText(analysis.description)
            self.chkAddToMap.setCheckState(Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

            # TODO: Set dropdowns when existing analysis

            # User cannot reassign mask once the analysis is created!
            self.cboMask.setEnabled(False)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Analysis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        mask = self.cboMask.currentData(Qt.UserRole)
        if mask is None:
            QMessageBox.warning(self, 'Missing Mask', 'You must select a mask to continue.')
            self.cboMask.setFocus()
            return()

        basemap = self.cboBasemap.currentData(Qt.UserRole)
        if basemap is None:
            QMessageBox.warning(self, 'Missing Basemap', 'You must select a basemap to continue.')
            self.cboBasemap.setFocus()
            return()

        if self.analysis is not None:
            try:
                self.analysis.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), basemap)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return
        else:
            try:
                self.analysis = insert_analysis(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), mask, basemap)
                self.project.analyses[self.analysis.id] = self.analysis
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "An analysis with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Analysis', str(ex))
                return

        super(FrmAnalysisProperties, self).accept()
