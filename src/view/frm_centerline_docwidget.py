"""
Doc Widget for building centerlines

"""
from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsProject, QgsLineString, QgsVectorLayer, QgsFeature, QgsGeometry, QgsMapLayer, QgsDistanceArea, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsMapToolIdentifyFeature

from ..gp.centerlines import CenterlineTask
from ..model.project import Project
from ..model.db_item import DBItem
from ..model.profile import Profile

from .capture_line_segment import LineSegmentMapTool
from .utilities import add_help_button
from .frm_save_centerline import FrmSaveCenterline


class FrmCenterlineDocWidget(QtWidgets.QDockWidget):

    export_complete = pyqtSignal(Profile or None, bool)

    def __init__(self, parent, project: Project, iface):

        super(FrmCenterlineDocWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        self.setupUi()

        self.project = project
        self.iface = iface
        self.parent = parent
        self.canvas = self.iface.mapCanvas()
        self.get_linestring = None
        # self.get_linestring = None
        self.polygon_layer = None

        self.d = QgsDistanceArea()
        self.d.setEllipsoid('WGS84')

        self.centerline_setup()

    def centerline_setup(self):

        self.feat_centerline = None
        self.geom_centerline = None
        self.geom_polygon = None
        self.geom_start = None
        self.geom_end = None
        self.densify_distance = None
        self.fields = None
        self.transform = None

        self.txtEnd.setText("")
        self.txtStart.setText("")
        self.txtPolygon.setText("")

        self.remove_cl_temp_layers()
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

    def configure_polygon(self, polygon_layer: DBItem):

        self.polygon_layer = polygon_layer
        self.txtLayer.setText(polygon_layer.name)
        fc_path = f'{polygon_layer.gpkg_path}|layername={polygon_layer.fc_name}'

        # Initially choose first feature here
        layer = QgsVectorLayer(fc_path, polygon_layer.fc_name, 'ogr')
        self.polygon_crs = layer.crs()
        feats = layer.getFeatures()
        feat = QgsFeature()
        feats.nextFeature(feat)
        self.geom_polygon = QgsGeometry(feat.geometry())
        self.txtPolygon.setText(f'FeatureID: {feat.id()}')

        epgs_canvas = self.canvas.mapSettings().destinationCrs().authid()
        sourceCrs = QgsCoordinateReferenceSystem(epgs_canvas)
        self.transform = QgsCoordinateTransform(sourceCrs, self.polygon_crs, QgsProject.instance())

    def remove_cl_temp_layers(self):
        map_layers = QgsProject.instance().mapLayers()
        for layer in map_layers:
            if map_layers[layer].name() in ["QRIS Centerline Preview", "QRIS Centerline Start Preview", "QRIS Centerline End Preview"]:
                QgsProject.instance().removeMapLayer(map_layers[layer].id())

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
        if self.geom_start is None or self.geom_end is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Capture the start and end of the polygon before generating centerline.')
            return
        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Load the polygon before generating centerline.')
            return

        self.layer_centerline.dataProvider().truncate()

        if self.geom_polygon.isMultipart():
            geom_polygon = QgsGeometry.fromMultiPolygonXY(self.geom_polygon.asMultiPolygon())
        else:
            geom_polygon = QgsGeometry.fromPolygonXY(self.geom_polygon.asPolygon())
        geom_start = self.geom_start.clone()
        geom_end = self.geom_end.clone()

        length = geom_polygon.get().perimeter()
        length_measure = self.d.measurePerimeter(geom_polygon)
        self.densify_distance = (self.dblDensity.value() / length_measure) * length

        centerline_task = CenterlineTask(geom_polygon, geom_start, geom_end, self.densify_distance)
        # DEBUG
        # result = centerline_task.run()
        # if result is True:
        #     cl = QgsGeometry(centerline_task.centerline)
        #     self.centerline_complete(cl)
        # PRODUCTION
        centerline_task.centerline_complete.connect(self.centerline_complete)
        QgsApplication.taskManager().addTask(centerline_task)

        return

    def cmdSaveCl_click(self):

        if self.feat_centerline is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Generate the centerline before saving.')
            return
        geom_centerline = self.feat_centerline.geometry()

        sline_length = self.d.measureLine(QgsPointXY(geom_centerline.get().points()[0]), QgsPointXY(geom_centerline.get().points()[-1]))
        geom_length = self.d.measureLength(geom_centerline)
        metrics = {'Length (m)': geom_length, 'Sinuosity': geom_length / sline_length}
        frm_save_centerline = FrmSaveCenterline(self, self.project, self.feat_centerline, metrics, self.fields)
        result = frm_save_centerline.exec_()

        if result == QtWidgets.QDialog.Accepted:
            self.centerline_setup()  # Reset the map
            self.export_complete.emit(frm_save_centerline.profile, True)
        return

    def cmdReset_click(self):
        self.centerline_setup()
        return

    @pyqtSlot(QgsFeature)
    def capture_polygon(self, selected_polygon_feature):

        self.geom_polygon = selected_polygon_feature.geometry()
        self.txtPolygon.setText(f'FeatureID: {selected_polygon_feature.id()}')
        self.canvas.unsetMapTool(self.get_polygon)
        self.get_polygon = None

    @pyqtSlot(QgsLineString)
    def capture_start(self, line_string):

        self.geom_start = line_string
        self.geom_start.transform(self.transform)
        self.txtStart.setText(self.geom_start.asWkt())
        feat = QgsFeature()
        feat.setGeometry(self.geom_start)
        self.layer_start_line.dataProvider().addFeature(feat)
        self.layer_start_line.commitChanges()
        self.canvas.refreshAllLayers()
        self.canvas.unsetMapTool(self.get_linestring)
        self.get_linestring = None

    @pyqtSlot(QgsLineString)
    def capture_end(self, line_string):

        self.geom_end = line_string
        self.geom_end.transform(self.transform)
        self.txtEnd.setText(self.geom_end.asWkt())
        feat = QgsFeature()
        feat.setGeometry(self.geom_end)
        self.layer_end_line.dataProvider().addFeature(feat)
        self.layer_end_line.commitChanges()
        self.canvas.refreshAllLayers()
        self.canvas.unsetMapTool(self.get_linestring)
        self.get_linestring = None

    @pyqtSlot(QgsGeometry)
    def centerline_complete(self, centerline):

        geom_centerline_raw = QgsGeometry(centerline)
        smoothing_iter = self.dblSmoothingIter.value()
        length = geom_centerline_raw.length()
        length_measure = self.d.measureLength(geom_centerline_raw)
        smoothing_dist = (self.dblSmoothingMin.value() / length_measure) * length
        smoothing_offset = self.dblSmoothingOffset.value()
        smoothing_angle = self.dblSmoothingAngle.value()

        if smoothing_iter == 0:
            self.geom_centerline = QgsGeometry(geom_centerline_raw)
        else:
            self.geom_centerline = QgsGeometry(geom_centerline_raw.smooth(smoothing_iter, smoothing_offset, smoothing_dist, smoothing_angle))

        self.feat_centerline = QgsFeature()
        geom = QgsGeometry(self.geom_centerline)
        self.feat_centerline.setGeometry(geom)

        self.fields = {
            'parent_polygon_type': self.polygon_layer.db_table_name,
            'parent_polygon_id': self.polygon_layer.id,
            'parent_polygon_fid': self.txtPolygon.text(),
            'start_line': self.geom_start.asWkt(),
            'end_line': self.geom_start.asWkt(),
            'densify_distance': self.densify_distance,
            'smoothing_iterations': smoothing_iter,
            'smoothing_offset': smoothing_offset,
            'smoothing_min_distance': smoothing_dist,
            'smoothing_max_angle': smoothing_angle
        }

        self.layer_centerline.dataProvider().addFeature(self.feat_centerline)
        self.layer_centerline.commitChanges()
        self.canvas.refreshAllLayers()

    def setupUi(self):

        self.setWindowTitle("Build Centerlines")

        self.dockWidgetContents = QtWidgets.QWidget(self)
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

        self.lblDensity = QtWidgets.QLabel()
        self.lblDensity.setText('Densify Distance')
        self.lblDensity.setToolTip('Densify the polygon by adding regularly placed extra nodes inside each segment so that the maximum distance between any two nodes does not exceed the specified distance')
        self.grid.addWidget(self.lblDensity, 4, 0, 1, 1)

        self.dblDensity = QtWidgets.QSpinBox()
        self.dblDensity.setValue(10)
        self.dblDensity.setSuffix(' m')
        self.dblDensity.setRange(0, 500)
        self.grid.addWidget(self.dblDensity, 4, 1, 1, 1)

        self.lblSmoothingIter = QtWidgets.QLabel()
        self.lblSmoothingIter.setText('Smoothing Iter.')
        self.lblSmoothingIter.setToolTip('number of smoothing iterations to run. More iterations results in a smoother geometry. Set to 0 for no smoothing.')
        self.grid.addWidget(self.lblSmoothingIter, 5, 0, 1, 1)

        self.dblSmoothingIter = QtWidgets.QSpinBox()
        self.dblSmoothingIter.setValue(10)
        self.dblSmoothingIter.setRange(0, 10)
        self.grid.addWidget(self.dblSmoothingIter, 5, 1, 1, 1)

        self.lblSmoothingOffset = QtWidgets.QLabel()
        self.lblSmoothingOffset.setText('Smoothing Offset')
        self.lblSmoothingOffset.setToolTip(f'fraction of line to create new vertices along, between 0 and 1.0, e.g., the default value of 0.25 will create new vertices 25% and 75% along each line segment of the geometry for each iteration. Smaller values result in “tighter” smoothing.')
        self.grid.addWidget(self.lblSmoothingOffset, 6, 0, 1, 1)

        self.dblSmoothingOffset = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingOffset.setDecimals(2)
        self.dblSmoothingOffset.setValue(0.25)
        self.dblSmoothingOffset.setSingleStep(0.05)
        self.dblSmoothingOffset.setRange(0, 1)
        self.grid.addWidget(self.dblSmoothingOffset, 6, 1, 1, 1)

        self.lblSmoothingMin = QtWidgets.QLabel()
        self.lblSmoothingMin.setText('Smoothing Min Dist.')
        self.lblSmoothingMin.setToolTip('minimum segment length to apply smoothing to')
        self.grid.addWidget(self.lblSmoothingMin, 7, 0, 1, 1)

        self.dblSmoothingMin = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingMin.setSuffix(' m')
        self.dblSmoothingMin.setDecimals(1)
        self.dblSmoothingMin.setRange(-1.0, 500.0)
        self.dblSmoothingMin.setValue(-1.0)
        self.dblSmoothingMin.setSingleStep(5)
        self.grid.addWidget(self.dblSmoothingMin, 7, 1, 1, 1)

        self.lblSmoothingAngle = QtWidgets.QLabel()
        self.lblSmoothingAngle.setText('Smoothing Max Angle')
        self.lblSmoothingAngle.setToolTip('maximum angle at node (0-180) at which smoothing will be applied')
        self.grid.addWidget(self.lblSmoothingAngle, 8, 0, 1, 1)

        self.dblSmoothingAngle = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingAngle.setSuffix(' degrees')
        self.dblSmoothingAngle.setDecimals(1)
        self.dblSmoothingAngle.setRange(0, 180)
        self.dblSmoothingAngle.setValue(180.0)

        self.grid.addWidget(self.dblSmoothingAngle, 8, 1, 1, 1)

        self.horizBottom = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizBottom, 9, 1, 1, 1)

        self.cmdGenerateCl = QtWidgets.QPushButton()
        self.cmdGenerateCl.setText('Generate Centerline')
        self.cmdGenerateCl.clicked.connect(self.cmdGenerateCl_click)
        self.horizBottom.addWidget(self.cmdGenerateCl)

        self.cmdSaveCl = QtWidgets.QPushButton()
        self.cmdSaveCl.setText('Save Centerline')
        self.cmdSaveCl.clicked.connect(self.cmdSaveCl_click)
        self.horizBottom.addWidget(self.cmdSaveCl)

        self.cmdReset = QtWidgets.QPushButton()
        self.cmdReset.setText('Reset')
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 10, 0, 1, 1)

        self.vert.addLayout(add_help_button(self, 'centerlines'))

        self.setWidget(self.dockWidgetContents)
