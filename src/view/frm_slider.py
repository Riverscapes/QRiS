from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.basemap import Raster
from ..model.project import Project
from .frm_layer_picker import FrmLayerPicker

from ..QRiS.method_to_map import build_raster_slider_layer, apply_raster_slider_value, get_raster_statistics


class FrmSlider(QtWidgets.QDockWidget):

    def __init__(self, parent, project: Project):
        super().__init__(parent)
        self.setupUi()

        self.project = project
        self.raster = None

    def configure_raster(self, raster: Raster):

        self.raster = raster
        self.txtSurface.setText(raster.name)
        build_raster_slider_layer(self.project, raster)
        min, max = get_raster_statistics(self.project, raster)

        self.valElevation.setMinimum(min)
        self.valElevation.setMaximum(max)

        self.slider.setMinimum(min)
        self.slider.setMaximum(max)

    def sliderElevationChange(self, value: float):
        apply_raster_slider_value(self.project, self.raster, value)
        self.valElevation.setValue(value)

    def spinBoxElevationChange(self, value: float):
        apply_raster_slider_value(self.project, self.raster, value)
        self.slider.setValue(int(value))

    def cmdSelect_click(self):
        frm = FrmLayerPicker(self, 'Select raster', [])
        result = frm.exec_()
        if result is not None and result != 0:
            self.raster = frm.layer

    def cmdExport_click(self):
        QtWidgets.QMessageBox.information(self, 'Not Implemented', 'Exporting is not yet implemented.')

    def setupUi(self):

        self.setWindowTitle('Raster Slider')

        self.dockWidgetContents = QtWidgets.QWidget()
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

        self.lblElevation = QtWidgets.QLabel()
        self.lblElevation.setText('Surface Value')
        self.grid.addWidget(self.lblElevation, 1, 0, 1, 1)

        self.valElevation = QtWidgets.QDoubleSpinBox()
        # self.valElevation.setSuffix('m')
        # self.valElevation.setMinimum(0)
        # self.valElevation.setMaximum(100)
        # self.valElevation.setSingleStep(0.1)
        self.valElevation.setDecimals(1)
        self.valElevation.valueChanged.connect(self.spinBoxElevationChange)
        self.grid.addWidget(self.valElevation, 1, 1, 1, 1)

        self.slider = QtWidgets.QSlider()
        self.slider.setMaximum(1000)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(100)
        self.slider.valueChanged.connect(self.sliderElevationChange)
        self.grid.addWidget(self.slider, 2, 1, 1, 1)

        self.cmdExport = QtWidgets.QPushButton()
        self.cmdExport.setText('Export')
        self.cmdExport.clicked.connect(self.cmdExport_click)
        self.grid.addWidget(self.cmdExport)

        self.setWidget(self.dockWidgetContents)