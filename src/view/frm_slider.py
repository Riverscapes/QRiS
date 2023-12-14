from PyQt5 import QtCore, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import QgsRasterBandStats

from ..model.scratch_vector import ScratchVector

from ..model.raster import Raster, RASTER_SLIDER_MACHINE_CODE
from ..model.project import Project
from .frm_layer_picker import FrmLayerPicker
from .frm_slider_scratch_vector import FrmSliderScratchVector
from .double_slider import DoubleSlider
from .utilities import add_help_button
from ..QRiS.qris_map_manager import QRisMapManager


class FrmSlider(QtWidgets.QDockWidget):

    export_complete = pyqtSignal(ScratchVector or None, bool)

    def __init__(self, parent, project: Project, map_manager: QRisMapManager):
        super().__init__(parent)
        self.increment = 1.0
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

    def increment_change(self):
        self.increment = self.valIncrement.value()
        self.valElevation.setSingleStep(self.increment)

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

        if frm.result() == QtWidgets.QDialog.Rejected:
            return

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

        self.lblSurface = QtWidgets.QLabel('Surface')
        self.grid.addWidget(self.lblSurface, 0, 0, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz, 0, 1, 1, 1)

        self.txtSurface = QtWidgets.QLineEdit()
        self.txtSurface.setReadOnly(True)
        self.horiz.addWidget(self.txtSurface)

        self.cmdSurface = QtWidgets.QPushButton('Select')
        self.cmdSurface.setToolTip('Select a raster layer')
        self.cmdSurface.clicked.connect(self.cmdSelect_click)
        self.horiz.addWidget(self.cmdSurface)

        self.lblSliderType = QtWidgets.QLabel('Threshold')
        self.lblSliderType.setToolTip('Select whether the highlighted area will be above or below the threshold value')
        self.grid.addWidget(self.lblSliderType, 1, 0, 1, 1)

        self.horizOptions = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizOptions, 1, 1, 1, 1)

        self.optAbove = QtWidgets.QRadioButton('Above Value')
        self.horizOptions.addWidget(self.optAbove)
        self.optBelow = QtWidgets.QRadioButton('Below Value')
        self.optBelow.setChecked(True)
        self.horizOptions.addWidget(self.optBelow)

        self.lblElevation = QtWidgets.QLabel('Surface Value')
        self.grid.addWidget(self.lblElevation, 2, 0, 1, 1)

        self.valElevation = QtWidgets.QDoubleSpinBox()
        self.valElevation.setSingleStep(self.increment)
        self.valElevation.setDecimals(2)
        self.valElevation.valueChanged.connect(self.spinBoxElevationChange)
        self.grid.addWidget(self.valElevation, 2, 1, 1, 1)

        self.slider = DoubleSlider(decimals=2)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setSingleStep(self.increment)
        self.slider.doubleValueChanged.connect(self.sliderElevationChange)
        self.grid.addWidget(self.slider, 3, 1, 1, 1)

        self.lblIncrement = QtWidgets.QLabel('Increment')
        self.lblIncrement.setToolTip('The increment value for the slider')
        self.grid.addWidget(self.lblIncrement, 4, 0, 1, 1)

        self.valIncrement = QtWidgets.QDoubleSpinBox()
        self.valIncrement.setSingleStep(0.1)
        self.valIncrement.setDecimals(2)
        self.valIncrement.setValue(self.increment)
        self.valIncrement.valueChanged.connect(self.increment_change)
        self.grid.addWidget(self.valIncrement, 4, 1, 1, 1)

        self.gridButtons = QtWidgets.QGridLayout()
        self.vert.addLayout(self.gridButtons)

        self.gridButtons.addWidget(add_help_button(self, 'raster-slider'), 0, 0, 1, 1)

        self.gridButtons.addItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum), 0, 1, 1, 1)

        self.cmdExport = QtWidgets.QPushButton('Export Polygon')
        self.cmdExport.setToolTip('Export the highlighted area as a polygon')
        self.cmdExport.clicked.connect(self.cmdExport_click)
        self.gridButtons.addWidget(self.cmdExport, 0, 2, 1, 1)

        self.setWidget(self.dockWidgetContents)
