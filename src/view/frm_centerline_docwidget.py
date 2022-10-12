"""
Doc Widget for building centerlines

"""
from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject, QgsLineString, QgsVectorLayer, QgsFeature, QgsMapLayer
from qgis.gui import QgsMapToolIdentifyFeature

from shapely.wkt import loads

from ..gp.centerlines import CenterlinesTask, generate_centerline
from ..model.project import Project
from .capture_line_segment import LineSegmentMapTool
from .utilities import add_help_button


class FrmCenterlineDocWidget(QtWidgets.QDockWidget):

    def __init__(self, parent, project: Project, iface):

        super().__init__(parent)
        self.setupUi()

        self.project = project
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.get_linestring = None
        self.get_linestring = None
        self.polygon_layer = None

        self.centerline_setup()

    def centerline_setup(self):

        self.centerline = None

        self.polygon_wkt = None
        self.start_wkt = None
        self.end_wkt = None

        self.generate_ready()

        self.txtEnd.setText("")
        self.txtStart.setText("")
        self.txtPolygon.setText("")

        map_layers = QgsProject.instance().mapLayers()
        for layer in map_layers:
            if map_layers[layer].name() in ["QRIS Centerline Preview", "QRIS Centerline Start Preview", "QRIS Centerline End Preview"]:
                QgsProject.instance().removeMapLayer(map_layers[layer].id())

        self.canvas.refresh()

        self.layer_centerline = QgsVectorLayer('linestring', "QRIS Centerline Preview", 'memory')
        self.layer_start_line = QgsVectorLayer('linestring', "QRIS Centerline Start Preview", 'memory')
        self.layer_end_line = QgsVectorLayer('linestring', "QRIS Centerline End Preview", 'memory')

        self.layer_centerline.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
        self.layer_start_line.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
        self.layer_end_line.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))

        self.layer_centerline.renderer().symbol().symbolLayer(0).setColor(QColor('darkblue'))
        self.layer_centerline.renderer().symbol().symbolLayer(0).setWidth(0.66)
        self.layer_start_line.renderer().symbol().symbolLayer(0).setColor(QColor('red'))
        self.layer_end_line.renderer().symbol().symbolLayer(0).setColor(QColor('red'))

        QgsProject.instance().addMapLayers([self.layer_centerline, self.layer_start_line, self.layer_end_line])

    def configure_polygon(self, polygon_layer):

        self.polygon_layer = polygon_layer
        self.txtLayer.setText(polygon_layer.name)
        fc_path = f'{polygon_layer.gpkg_path}|layername={polygon_layer.fc_name}'

        # Initially choose first feature here
        layer = QgsVectorLayer(fc_path, polygon_layer.fc_name, 'ogr')
        feats = layer.getFeatures()
        feat = QgsFeature()
        feats.nextFeature(feat)
        geom_polygon = feat.geometry()
        self.polygon_wkt = geom_polygon.asWkt()
        self.txtPolygon.setText(f'FeatureID: {feat.id()}')

    def cmdSelect_click(self):

        layers = QgsProject.instance().mapLayersByName(self.polygon_layer.name)
        layer = layers[0]
        self.get_polygon = QgsMapToolIdentifyFeature(self.canvas, layer)
        self.canvas.setMapTool(self.get_polygon)
        self.get_polygon.featureIdentified.connect(self.capture_polygon)

    def cmdCaptureStart_click(self):

        self.layer_start_line.dataProvider().truncate()
        self.get_linestring = LineSegmentMapTool(self.canvas)
        self.canvas.setMapTool(self.get_linestring)
        self.get_linestring.line_captured.connect(self.capture_start)

    def cmdCaptureEnd_click(self):

        self.layer_end_line.dataProvider().truncate()
        self.get_linestring = LineSegmentMapTool(self.canvas)
        self.canvas.setMapTool(self.get_linestring)
        self.get_linestring.line_captured.connect(self.capture_end)

    def cmdGenerateCl_click(self):
        if self.start_wkt is None or self.end_wkt is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Capture the start and end of the polygon before generating centerline.')
            return

        if self.polygon_wkt is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Load the polygon before generating centerline.')

        self.layer_centerline.dataProvider().truncate()

        polygon = loads(self.polygon_wkt)
        start_line = loads(self.start_wkt)
        end_line = loads(self.end_wkt)

        self.centerline = generate_centerline(polygon, start_line, end_line)
        self.centerline_complete(self.centerline)
        # centerline_task = CenterlinesTask(self.polygon_wkb.data(), self.start_wkb.data(), self.end_wkb.data())
        # centerline_task.centerline_complete.connect(self.centerline_complete)

        # self.cmdExport.setEnabled(False)
        # QgsApplication.taskManager().addTask(centerline_task)

    def cmdSaveCl_click(self):

        QtWidgets.QMessageBox.information(self, 'Not Implemented', 'Exporting is not yet implemented.')

    def cmdReset_click(self):

        self.centerline_setup()

    def generate_ready(self):

        if all([val is not None for val in [self.polygon_wkt, self.start_wkt, self.end_wkt]]):
            self.cmdGenerateCl.setEnabled(True)
        else:
            self.cmdGenerateCl.setEnabled(False)

        if self.centerline is None:
            self.cmdSaveCl.setEnabled(False)
        else:
            self.cmdSaveCl.setEnabled(True)

    @pyqtSlot(QgsFeature)
    def capture_polygon(self, selected_polygon_feature):

        geom_polygon = selected_polygon_feature.geometry()
        self.polygon_wkt = geom_polygon.asWkt()

        self.txtPolygon.setText(f'FeatureID: {selected_polygon_feature.id()}')

        self.canvas.unsetMapTool(self.get_polygon)
        self.get_polygon = None
        self.generate_ready()

    @pyqtSlot(QgsLineString)
    def capture_start(self, line_string):

        self.start_wkt = line_string.asWkt()
        self.txtStart.setText(line_string.asWkt())
        feat = QgsFeature()
        feat.setGeometry(line_string)
        self.layer_start_line.dataProvider().addFeature(feat)
        self.layer_start_line.commitChanges()
        self.canvas.refreshAllLayers()

        self.canvas.unsetMapTool(self.get_linestring)
        self.get_linestring = None
        self.generate_ready()

    @pyqtSlot(QgsLineString)
    def capture_end(self, line_string):

        self.end_wkt = line_string.asWkt()
        self.txtEnd.setText(line_string.asWkt())
        feat = QgsFeature()
        feat.setGeometry(line_string)
        self.layer_end_line.dataProvider().addFeature(feat)
        self.layer_end_line.commitChanges()
        self.canvas.refreshAllLayers()

        self.canvas.unsetMapTool(self.get_linestring)
        self.get_linestring = None
        self.generate_ready()

    @pyqtSlot(str)
    def centerline_complete(self, centerline):

        geom_centerline = QgsLineString()
        geom_centerline.fromWkt(centerline.wkt)
        feat = QgsFeature()
        feat.setGeometry(geom_centerline)
        self.layer_centerline.dataProvider().addFeature(feat)
        self.layer_centerline.commitChanges()
        self.canvas.refreshAllLayers()

        self.centerline = centerline
        self.generate_ready()

    def setupUi(self):

        self.setWindowTitle("Build Centerlines")

        self.dockWidgetContents = QtWidgets.QWidget()
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblLayer = QtWidgets.QLabel()
        self.lblLayer.setText('Layer')
        self.grid.addWidget(self.lblLayer, 0, 0, 1, 1)

        self.txtLayer = QtWidgets.QLineEdit()
        self.txtLayer.setReadOnly(True)
        self.grid.addWidget(self.txtLayer, 0, 1, 1, 1)

        self.lblPolygon = QtWidgets.QLabel()
        self.lblPolygon.setText('Polygon')
        self.grid.addWidget(self.lblPolygon, 1, 0, 1, 1)

        self.horizPoly = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizPoly, 1, 1, 1, 1)

        self.txtPolygon = QtWidgets.QLineEdit()
        self.txtPolygon.setReadOnly(True)
        self.horizPoly.addWidget(self.txtPolygon)

        self.cmdPolygon = QtWidgets.QPushButton()
        self.cmdPolygon.setText('Select')
        self.cmdPolygon.clicked.connect(self.cmdSelect_click)
        self.horizPoly.addWidget(self.cmdPolygon)

        self.lblStart = QtWidgets.QLabel()
        self.lblStart.setText('Start of Polygon')
        self.grid.addWidget(self.lblStart, 2, 0, 1, 1)

        self.horizStart = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizStart, 2, 1, 1, 1)

        self.txtStart = QtWidgets.QLineEdit()
        self.txtStart.setReadOnly(True)
        self.horizStart.addWidget(self.txtStart)

        self.cmdCaptureS = QtWidgets.QPushButton()
        self.cmdCaptureS.setText('Capture')
        self.cmdCaptureS.clicked.connect(self.cmdCaptureStart_click)
        self.horizStart.addWidget(self.cmdCaptureS)

        self.lblEnd = QtWidgets.QLabel()
        self.lblEnd.setText('End of Polygon')
        self.grid.addWidget(self.lblEnd, 3, 0, 1, 1)

        self.horizEnd = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizEnd, 3, 1, 1, 1)

        self.txtEnd = QtWidgets.QLineEdit()
        self.txtEnd.setReadOnly(True)
        self.horizEnd.addWidget(self.txtEnd)

        self.cmdCaptureE = QtWidgets.QPushButton()
        self.cmdCaptureE.setText('Capture')
        self.cmdCaptureE.clicked.connect(self.cmdCaptureEnd_click)
        self.horizEnd.addWidget(self.cmdCaptureE)

        self.lblSmoothing = QtWidgets.QLabel()
        self.lblSmoothing.setText('Smoothing')
        self.grid.addWidget(self.lblSmoothing, 4, 0, 1, 1)

        self.dblSmoothing = QtWidgets.QDoubleSpinBox()
        self.dblSmoothing.setDecimals(1)
        self.dblSmoothing.setValue(10)
        self.dblSmoothing.setRange(0, 500)
        self.grid.addWidget(self.dblSmoothing, 4, 1, 1, 1)

        self.horizBottom = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizBottom, 5, 1, 1, 1)

        self.cmdGenerateCl = QtWidgets.QPushButton()
        self.cmdGenerateCl.setText('Generate Centerline')
        self.cmdGenerateCl.clicked.connect(self.cmdGenerateCl_click)
        self.horizBottom.addWidget(self.cmdGenerateCl)

        self.cmdSaveCl = QtWidgets.QPushButton()
        self.cmdSaveCl.setText('Save Centerline')
        self.cmdSaveCl.clicked.connect(self.cmdSaveCl_click)
        self.cmdSaveCl.setEnabled(False)
        self.horizBottom.addWidget(self.cmdSaveCl)

        self.cmdReset = QtWidgets.QPushButton()
        self.cmdReset.setText('Reset')
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 6, 0, 1, 1)

        self.vert.addLayout(add_help_button(self, 'centerline'))

        self.setWidget(self.dockWidgetContents)
