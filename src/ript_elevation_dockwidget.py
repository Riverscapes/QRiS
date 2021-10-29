import os

from qgis.core import QgsRasterLayer, QgsProject, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor

from .export_elev_surface_dialog import ExportElevationSurfaceDlg
from .qris_project import QRiSProject

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_dockwidget_elevation.ui'))


class RIPTElevationDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, raster, ript_project, parent=None):
        """Constructor."""
        super(RIPTElevationDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.ript_project = ript_project
        self.raster = raster
        self.elevation_value = 1.0

        self.txtRasterName.setText(self.raster.name)

        self.raster_path = os.path.join(self.ript_project.project_path, raster.path)
        self.group_layer = None
        self.raster_layer = QgsRasterLayer(self.raster_path, 'Elevation Explorer')
        self.base_raster_layer = QgsRasterLayer(self.raster_path, self.raster.name)
        self.base_raster_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), "..", 'resources', 'symbology', 'hand.qml'))

        self.updateElevationLayer(self.elevation_value)

        QgsProject.instance().addMapLayer(self.base_raster_layer)
        QgsProject.instance().addMapLayer(self.raster_layer)

        # TODO Get min max of raster and apply to slider tools

        self.elevationSlider.valueChanged.connect(self.sliderElevationChange)
        self.numElevation.valueChanged.connect(self.spinBoxElevationChange)
        self.btnExport.clicked.connect(self.exportPolygonDlg)
        self.closingPlugin.connect(self.closeWidget)

    def updateElevationLayer(self, value=1.0):
        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(value, QColor(255, 20, 225), f'Elevation {value}')])
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)
        renderer = QgsSingleBandPseudoColorRenderer(self.raster_layer.dataProvider(), 1, shader)
        self.raster_layer.setRenderer(renderer)
        self.raster_layer.triggerRepaint()

    def sliderElevationChange(self, value):
        self.elevation_value = value / 10
        self.updateElevationLayer(value / 10)
        self.numElevation.setValue(value / 10)

    def spinBoxElevationChange(self, value):
        self.elevation_value = value
        self.updateElevationLayer(value)
        self.elevationSlider.setValue(int(value * 10))

    def exportPolygonDlg(self):
        self.export_dlg = ExportElevationSurfaceDlg(self.raster, self.elevation_value, self.ript_project)
        self.export_dlg.dataChange.connect(self.exportPolgyon)
        self.export_dlg.show()

    def exportPolgyon(self, updated_project, surface_name):
        self.ript_project = updated_project
        self.dataChange.emit(self.ript_project, surface_name)
        self.closeWidget()
        return

    def closeWidget(self):
        QgsProject.instance().removeMapLayer(self.base_raster_layer.id())
        QgsProject.instance().removeMapLayer(self.raster_layer.id())
        self.close()
        self.destroy()
        return
