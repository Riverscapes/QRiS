import os
import json

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis

from .qris_project import QRiSProject

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_add_detrended.ui'))


class AddDetrendedRasterDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, parent=None, raster_path=None, qris_project=None):
        """Constructor."""
        QDialog.__init__(self, parent)  # raster_path, qris_project)
        self.setupUi(self)

        self.qris_project = qris_project
        self.raster = raster_path
        self.raster_name = os.path.basename(self.raster).rstrip('.tif')

        self.txtRasterName.setText(self.raster_name)
        self.txtOriginalRasterPath.setText(raster_path)
        self.text_validate()

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

        self.txtRasterName.textChanged.connect(self.text_validate)
        # self.btnSaveFolder.clicked.connect(self.openFolderDlg)
        self.buttonBox.accepted.connect(self.save_raster)

    def text_validate(self):

        text = self.txtRasterName.text()
        out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_") + ".tif"
        self.txtProjectRasterPath.setText(os.path.join(f"DET{str(len(self.qris_project.detrended_rasters) + 1).zfill(4)}", out_text))
        self.raster_name = self.txtRasterName.text()

    def save_raster(self):

        out_raster = os.path.join(self.qris_project.project_path, "DetrendedRasters", self.txtProjectRasterPath.text())

        if not os.path.exists(os.path.dirname(out_raster)):
            os.makedirs(os.path.dirname(out_raster))

        ds = gdal.Open(self.txtOriginalRasterPath.text())
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.CreateCopy(out_raster, ds, strict=True)
        out_ds = None

        self.qris_project.add_detrended(self.raster_name, out_raster)
        self.qris_project.export_project_file()

        self.dataChange.emit(self.qris_project, self.raster_name)

        return out_raster
