from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import QgsRasterBandStats

from ..model.scratch_vector import ScratchVector

from ..model.raster import Raster, RASTER_SLIDER_MACHINE_CODE
from ..model.project import Project
from .frm_layer_picker import FrmLayerPicker
from .frm_slider_scratch_vector import FrmSliderScratchVector
from .double_slider import DoubleSlider

from ..QRiS.qris_map_manager import QRisMapManager


class FrmSlider(QtWidgets.QDockWidget):

    export_complete = pyqtSignal(ScratchVector or None, bool)

    def __init__(self, parent, project: Project, map_manager: QRisMapManager):
        super().__init__(parent)
        self.setupUi()

        self.project = project
        self.map_manager = map_manager
        self.raster = None
        self.raster_layer = None
        self.scratch_vector = None
        self.max = None

        self.optAbove.toggled.connect(self.invert_values)

    def configure_raster(self, raster: Raster):

        self.raster = raster
        self.txtSurface.setText(raster.name)
        self.raster_layer = self.map_manager.build_raster_slider_layer(raster)
        min = self.raster_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.Min, self.raster_layer.extent(), 0).minimumValue
        max = self.raster_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.Max, self.raster_layer.extent(), 0).maximumValue
        self.max = max
        self.valElevation.setMinimum(min)
        self.valElevation.setMaximum(max)
        self.valElevation.setValue(min)
        self.sliderElevationChange(self.valElevation.value())

        self.slider.setMinimum(min)
        self.slider.setMaximum(max)

    def sliderElevationChange(self, value: float):
        self.map_manager.apply_raster_single_value(self.raster_layer, value, self.max, self.optAbove.isChecked())
        self.valElevation.setValue(value)

    def spinBoxElevationChange(self, value: float):
        self.map_manager.apply_raster_single_value(self.raster_layer, value, self.max, self.optAbove.isChecked())
        self.slider.setValue(value)

    def invert_values(self):
        value = self.valElevation.value()
        self.map_manager.apply_raster_single_value(self.raster_layer, value, self.max, self.optAbove.isChecked())

    def cmdSelect_click(self):
        rasters = list(self.project.rasters.values())
        frm = FrmLayerPicker(self, 'Select raster', rasters)
        result = frm.exec_()
        if result is not None and result != 0:
            self.configure_raster(frm.layer)

    def cmdExport_click(self):

        raster_path = self.project.get_absolute_path(self.raster.path)
        threshold_value = self.valElevation.value()

        frm = FrmSliderScratchVector(self, self.project, raster_path, threshold_value, self.optAbove.isChecked())
        frm.exec_()

        self.add_to_map = frm.chkAddToMap.isChecked()
        self.scratch_vector = frm.scratch_vector

        self.export_complete.emit(self.scratch_vector, self.add_to_map)

    def closeEvent(self, event):
        self.map_manager.remove_machine_code_layer(self.project.map_guid, RASTER_SLIDER_MACHINE_CODE)
        QtWidgets.QDockWidget.closeEvent(self, event)

    def setupUi(self):

        self.setWindowTitle('Raster Slider')

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.dockWidgetContents = QtWidgets.QWidget(self)
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblSurface = QtWidgets.QLabel()
        self.lblSurface.setText('Surface')
        self.grid.addWidget(self.lblSurface, 0, 0, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz, 0, 1, 1, 1)

        self.txtSurface = QtWidgets.QLineEdit()
        self.txtSurface.setReadOnly(True)
        self.horiz.addWidget(self.txtSurface)

        self.cmdSurface = QtWidgets.QPushButton()
        self.cmdSurface.setText('Select')
        self.cmdSurface.clicked.connect(self.cmdSelect_click)
        self.horiz.addWidget(self.cmdSurface)

        self.lblSliderType = QtWidgets.QLabel('Threshold')
        self.grid.addWidget(self.lblSliderType, 1, 0, 1, 1)

        self.horizOptions = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizOptions, 1, 1, 1, 1)

        self.optAbove = QtWidgets.QRadioButton('Above Value')
        self.horizOptions.addWidget(self.optAbove)
        self.optBelow = QtWidgets.QRadioButton('Below Value')
        self.optBelow.setChecked(True)
        self.horizOptions.addWidget(self.optBelow)

        self.lblElevation = QtWidgets.QLabel()
        self.lblElevation.setText('Surface Value')
        self.grid.addWidget(self.lblElevation, 2, 0, 1, 1)

        self.valElevation = QtWidgets.QDoubleSpinBox()
        self.valElevation.setSingleStep(0.1)
        self.valElevation.setDecimals(2)
        self.valElevation.valueChanged.connect(self.spinBoxElevationChange)
        self.grid.addWidget(self.valElevation, 2, 1, 1, 1)

        self.slider = DoubleSlider(decimals=2)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setSingleStep(0.1)
        self.slider.doubleValueChanged.connect(self.sliderElevationChange)
        self.grid.addWidget(self.slider, 3, 1, 1, 1)

        self.precision = QtWidgets

        self.cmdExport = QtWidgets.QPushButton()
        self.cmdExport.setText('Export')
        self.cmdExport.clicked.connect(self.cmdExport_click)
        self.grid.addWidget(self.cmdExport)

        self.setWidget(self.dockWidgetContents)
