"""
Doc Widget for building centerlines

"""
from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsProject, QgsLineString, QgsFeature, QgsGeometry, QgsDistanceArea, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.utils import iface

from ..gp.centerlines import CenterlineTask
from ..model.project import Project
from ..model.db_item import DBItem
from ..model.profile import Profile

from .capture_line_segment import LineSegmentMapTool
from .utilities import add_help_button
from .frm_save_centerline import FrmSaveCenterline
from ..QRiS.qris_map_manager import QRisMapManager

PREVIEW_STARTLINE_MACHINE_CODE = "Startline Preview"
PREVIEW_ENDLINE_MACHINE_CODE = "Endline Preview"
PREVIEW_CENTERTLINE_MACHINE_CODE = "Centerline Preview"


class FrmCenterlineDocWidget(QtWidgets.QDockWidget):

    export_complete = pyqtSignal(Profile or None, bool)

    def __init__(self, parent, project: Project, map_manager: QRisMapManager):

        super(FrmCenterlineDocWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        self.setupUi()

        self.project = project
        self.map_manager = map_manager

        self.get_startline = LineSegmentMapTool(iface.mapCanvas())
        self.get_endline = LineSegmentMapTool(iface.mapCanvas())
        self.get_startline.line_captured.connect(self.capture_start)
        self.get_endline.line_captured.connect(self.capture_end)

        self.d = QgsDistanceArea()
        self.d.setEllipsoid('WGS84')

    def centerline_setup(self, polygon_source: DBItem):

        self.feat_centerline = None
        self.geom_centerline = None
        self.geom_polygon = None
        self.geom_start = None
        self.geom_end = None
        self.densify_distance = None
        self.fields = None
        self.transform = None
        self.polygon_source = polygon_source
        self.polygon_layer = self.map_manager.get_db_item_layer(self.project.map_guid, self.polygon_source, None).layer()
        iface.setActiveLayer(self.polygon_layer)
        iface.mapCanvas().selectionChanged.connect(self.capture_polygon)

        self.txtLayer.setText(self.polygon_source.name)
        self.capture_polygon()  # This should get the selection, if there are selected features in the polygon layer already
        self.txtStart.setText("")
        self.txtEnd.setText("")

        self.polygon_crs = self.polygon_layer.crs()
        canvas_crs = QgsCoordinateReferenceSystem(iface.mapCanvas().mapSettings().destinationCrs().authid())
        self.transform = QgsCoordinateTransform(canvas_crs, self.polygon_crs, QgsProject.instance())

        self.d.setSourceCrs(self.polygon_crs, QgsProject.instance().transformContext())

        # Set up the Preview Layers
        self.remove_preview_layers()
        iface.mapCanvas().refresh()
        layer_uri = f'linestring?crs={self.polygon_crs.authid()}'

        self.layer_centerline = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_CENTERTLINE_MACHINE_CODE, "QRIS Centerline Preview", driver='memory')
        self.layer_start_line = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_STARTLINE_MACHINE_CODE, "QRIS Centerline Start Preview", driver='memory')
        self.layer_end_line = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_ENDLINE_MACHINE_CODE, "QRIS Centerline End Preview", driver='memory')

        self.layer_centerline.renderer().symbol().symbolLayer(0).setColor(QColor('darkblue'))
        self.layer_centerline.renderer().symbol().symbolLayer(0).setWidth(0.66)
        self.layer_start_line.renderer().symbol().symbolLayer(0).setColor(QColor('red'))
        self.layer_end_line.renderer().symbol().symbolLayer(0).setColor(QColor('red'))

        self.layer_centerline.triggerRepaint()
        self.layer_start_line.triggerRepaint()
        self.layer_end_line.triggerRepaint()
        iface.mapCanvas().refresh()

        # self.cmdSelectPolygon_click()

    def remove_preview_layers(self):
        for machine_code in [PREVIEW_STARTLINE_MACHINE_CODE, PREVIEW_CENTERTLINE_MACHINE_CODE, PREVIEW_ENDLINE_MACHINE_CODE]:
            self.map_manager.remove_machine_code_layer(self.project.map_guid, machine_code)

    def cmdSelectPolygon_click(self):
        iface.setActiveLayer(self.polygon_layer)
        iface.mapCanvas().selectionChanged.connect(self.capture_polygon)
        self.action = iface.actionSelect()
        self.action.trigger()

    def cmdCaptureStart_click(self):
        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Select one and only one polygon feature before capturing the starting/ending locations.')
            return
        self.layer_start_line.dataProvider().truncate()
        iface.mapCanvas().setMapTool(self.get_startline)

    def cmdCaptureEnd_click(self):
        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Select one and only one polygon feature before capturing the starting/ending locations.')
            return
        self.layer_end_line.dataProvider().truncate()
        iface.mapCanvas().setMapTool(self.get_endline)

    def cmdGenerateCl_click(self):

        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Select one and only one polygon feature before generating centerline.')
            return
        if self.geom_start is None or self.geom_end is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Capture the start and end of the polygon before generating centerline.')
            return
        if not all([self.geom_polygon.intersects(QgsGeometry().fromPolyline(self.geom_start)), self.geom_polygon.intersects(QgsGeometry().fromPolyline(self.geom_end))]):
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Make sure both start and stop lines intersect the polygon.')
            return
        if not self.geom_polygon.isGeosValid():
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'The polygon is not GEOS valid. Please fix it before generating centerline.')
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
        result = centerline_task.run()
        if result is True:
            cl = QgsGeometry(centerline_task.centerline)
            self.centerline_complete(cl)
        # PRODUCTION
        # centerline_task.centerline_complete.connect(self.centerline_complete)
        # QgsApplication.taskManager().addTask(centerline_task)

        return

    def cmdSaveCenterline_click(self):

        if self.feat_centerline is None:
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Generate the centerline before saving.')
            return
        geom_centerline = self.feat_centerline.geometry()
        if geom_centerline.isMultipart():
            QtWidgets.QMessageBox.information(self, 'Centerlines Error', 'Unable to save a multipart centerline.')
            return

        transform = QgsCoordinateTransform(self.polygon_crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
        geom_centerline.transform(transform)

        sline_length = self.d.measureLine(QgsPointXY(geom_centerline.get().points()[0]), QgsPointXY(geom_centerline.get().points()[-1]))
        geom_length = self.d.measureLength(geom_centerline)
        metrics = {'Length (m)': geom_length, 'Sinuosity': geom_length / sline_length}
        frm_save_centerline = FrmSaveCenterline(self, self.project, geom_centerline, metrics, self.fields)
        result = frm_save_centerline.exec_()

        if result == QtWidgets.QDialog.Accepted:
            self.centerline_setup(self.polygon_source)  # Reset the map
            self.export_complete.emit(frm_save_centerline.profile, True)
        return

    def cmdReset_click(self):
        self.centerline_setup(self.polygon_source)
        return

    @pyqtSlot()
    def capture_polygon(self):

        features = self.polygon_layer.selectedFeatures()

        if len(features) == 1:
            self.geom_polygon = features[0].geometry()
            self.txtPolygon.setText(f'FeatureID: {features[0].id()}')
        elif len(features) == 0:
            self.geom_polygon = None
            self.txtPolygon.setText(f'No Features Selected')
        else:
            self.geom_polygon = None
            self.txtPolygon.setText(f'Multiple Features Selected')

    @pyqtSlot(QgsLineString)
    def capture_start(self, line_string):
        self.geom_start = line_string
        self.geom_start.transform(self.transform)
        self.txtStart.setText(self.geom_start.asWkt())
        feat = QgsFeature()
        feat.setGeometry(self.geom_start)
        self.layer_start_line.dataProvider().addFeature(feat)
        self.layer_start_line.commitChanges()
        self.layer_start_line.triggerRepaint()
        iface.mapCanvas().unsetMapTool(self.get_startline)

    @pyqtSlot(QgsLineString)
    def capture_end(self, line_string):
        self.geom_end = line_string
        self.geom_end.transform(self.transform)
        self.txtEnd.setText(self.geom_end.asWkt())
        feat = QgsFeature()
        feat.setGeometry(self.geom_end)
        self.layer_end_line.dataProvider().addFeature(feat)
        self.layer_end_line.commitChanges()
        self.layer_end_line.triggerRepaint()
        iface.mapCanvas().unsetMapTool(self.get_endline)

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
            'parent_polygon_type': self.polygon_source.db_table_name,
            'parent_polygon_id': self.polygon_source.id,
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
        self.layer_centerline.triggerRepaint()
        iface.mapCanvas().refresh()

    def closeEvent(self, event):
        self.remove_preview_layers()
        QtWidgets.QDockWidget.closeEvent(self, event)

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
        self.cmdPolygon.clicked.connect(self.cmdSelectPolygon_click)
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
        self.cmdSaveCl.clicked.connect(self.cmdSaveCenterline_click)
        self.horizBottom.addWidget(self.cmdSaveCl)

        self.cmdReset = QtWidgets.QPushButton()
        self.cmdReset.setText('Reset')
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 10, 0, 1, 1)

        self.vert.addLayout(add_help_button(self, 'centerlines'))

        self.setWidget(self.dockWidgetContents)
