import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis, QgsFeature, QgsVectorLayer

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table

from .ui.assessment import Ui_Assessment


class FrmNewProject(QDialog, Ui_Assessment):

    def __init__(self, parent=None):
        super(FrmNewProject, self).__init__(parent)
        self.setupUi(self)
