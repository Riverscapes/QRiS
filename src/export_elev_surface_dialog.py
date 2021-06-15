import os
import json

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis

from .ript_project import RiptProject
from .gp.vectorize import raster_to_polygon

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_export_elevation_surface.ui'))

surface_types = ['valley bottom', 'active floodplain', 'inactive floodplain', 'zone of influence', 'other']


class ExportElevationSurfaceDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(RiptProject, str)

    def __init__(self, raster, elevation_value, ript_project, parent=None):
        """Constructor."""
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.project = ript_project
        self.raster = raster
        self.elevation_value = elevation_value
        self.surface_name = f"Surface From {raster.name} at Detrended Elevation {elevation_value} m"
        self.surface_name_short = f"Surface{str(len(self.raster.surfaces.values()) + 1).zfill(4)}"
        self.gpkg = os.path.join(ript_project.project_path, os.path.dirname(self.raster.path), "Surfaces.gpkg")

        self.txtSurfaceName.setText(self.surface_name)
        self.txtSurfacePath.setText(os.path.join(os.path.dirname(self.raster.path), "Surfaces.gpkg", self.surface_name_short))
        self.cboSurfaceType.addItems(surface_types)
        # self.text_validate()

        self.buttonBox.button(QDialogButtonBox.Save).setEnabled(True)

        # self.txtSurfaceName.textChanged.connect(self.text_validate)
        # self.btnSaveFolder.clicked.connect(self.openFolderDlg)
        self.buttonBox.accepted.connect(self.save_surface)

    def text_validate(self):

        #text = self.txtSurfaceName.text()
        # out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")

        self.txtProjectRasterPath.setText(self.surface_name)

    def save_surface(self):

        if not os.path.exists(os.path.dirname(self.gpkg)):
            os.makedirs(os.path.dirname(self.gpkg))

        raster_to_polygon(os.path.join(self.project.project_path, self.raster.path), self.gpkg, self.surface_name_short, self.elevation_value, surface_name=str(self.cboSurfaceType.currentText()))

        self.raster.add_surface(self.surface_name, self.txtSurfacePath.text(), str(self.cboSurfaceType.currentText()))
        self.project.detrended_rasters[self.raster.name] = self.raster

        self.project.export_project_file()

        self.dataChange.emit(self.project, self.surface_name)
