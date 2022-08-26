from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsRasterLayer, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer

from ..model.project import Project
from .frm_layer_picker import FrmLayerPicker


class FrmSlider(QtWidgets.QDocWidget):

    def __init__(self, parent, project: Project):
        super().__init__(parent)
        self.setupUi()

        self.project = project

    def sliderElevationChange(self, value):
        self.elevation_value = value / 10
        self.updateElevationLayer(value / 10)
        self.numElevation.setValue(value / 10)

    def spinBoxElevationChange(self, value):
        self.elevation_value = value
        self.updateElevationLayer(value)
        self.slider.setValue(int(value * 10))

    def updateElevationLayer(self, value=1.0):
        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(value, QtGui.QColor(255, 20, 225), f'Elevation {value}')])
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)
        # renderer = QgsSingleBandPseudoColorRenderer(self.raster_layer.dataProvider(), 1, shader)
        # self.raster_layer.setRenderer(renderer)
        # self.raster_layer.triggerRepaint()

    def cmdSelect_click(self):

        frm = FrmLayerPicker('Select raster', [])
        result = frm.exec_()
        if result is not None and result != 0:
            self.surface = None
            print('todo')

    def cmdExport_click(self):

        QtWidgets.QMessageBox.information(self, 'Not Implemented', 'Exporting is not yet implemented.')

    def setupUi(self):

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblSurface = QtWidgets.QLabel()
        self.lblSurface.setText('Surface')
        self.grid.addWidget(self.lblSurface, 0, 0, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz, 0, 1, 1, 1)

        self.txtSurface = QtWidgets.QLineEdit()
        self.txtSurface.setReadOnly(True)
        self.horiz(self.txtSurface)

        self.cmdSurface = QtWidgets.QPushButton()
        self.cmdSurface.setText('Select')
        self.cmdExport.clicked.connect(self.cmdSelect_click)
        self.horiz.addWidget(self.cmdSurface)

        self.lblElevation = QtWidgets.QLabel()
        self.lblElevation.setText('Surface Value')
        self.grid.addWidget(1, 0, 1, 1)

        self.valElevation = QtWidgets.QDoubleSpinBox()
        # self.valElevation.setSuffix('m')
        # self.valElevation.setMinimum(0)
        # self.valElevation.setMaximum(100)
        # self.valElevation.setSingleStep(0.1)
        self.valElevation.setDecimals(1)
        self.grid.addWidget(self.valElevation, 1, 1, 1, 1)

        self.slider = QtWidgets.QSlider()
        self.slider.maximum(1000)
        self.slider.orientation(QtCore.Qt.Horizontal)
        self.slider.tickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.tickInterval(100)
        self.grid.addWidget(self.slider, 2, 1, 1, 1)

        self.cmdExport = QtWidgets.QPushButton()
        self.cmdExport.setText('Export')
        self.cmdExport.clicked.connect(self.cmdExport_click)
        self.grid.addWidget(self.cmdExport)
