"""
Doc Widget for building centerlines

"""

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea, QgsFeature, QgsGeometry, QgsLineString, QgsPointXY, QgsProject, QgsVectorLayer
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QColor

from ..compat import DLG_ACCEPTED, MESSAGE_LEVEL_CRITICAL, SPSZ_EXPANDING, SPSZ_MINIMUM, WA_QUIT_ON_CLOSE
from ..gp.centerlines import CenterlineTask
from ..lib.map import get_utm_crs
from ..model.db_item import DBItem
from ..model.layer import Layer
from ..model.profile import Profile
from ..model.project import Project
from ..QRiS.qris_map_manager import QRisMapManager
from ..QRiS.settings import Settings
from .frm_layer_picker import FrmLayerPicker
from .frm_profile import FrmProfile
from .utilities import add_help_button
from .widgets.capture_line_segment import LineSegmentMapTool

PREVIEW_STARTLINE_MACHINE_CODE = "Startline Preview"
PREVIEW_ENDLINE_MACHINE_CODE = "Endline Preview"
PREVIEW_CENTERTLINE_MACHINE_CODE = "Centerline Preview"


class FrmCenterlineDocWidget(QtWidgets.QDockWidget):
    export_complete = pyqtSignal(Profile or None, bool)

    def __init__(self, parent, project: Project, map_manager: QRisMapManager):

        super().__init__(parent)
        self.setAttribute(WA_QUIT_ON_CLOSE)
        self.setupUi()

        self.project = project
        self.map_manager = map_manager

        self.get_startline = LineSegmentMapTool(Settings().iface.mapCanvas())
        self.get_endline = LineSegmentMapTool(Settings().iface.mapCanvas())
        self.get_startline.line_captured.connect(self.capture_start)
        self.get_endline.line_captured.connect(self.capture_end)

        self.d = QgsDistanceArea()
        self.d.setEllipsoid("WGS84")

    def centerline_setup(self, polygon_source: DBItem):

        self.feat_centerline: QgsFeature = None
        self.geom_centerline: QgsGeometry = None
        self.geom_polygon: QgsGeometry = None
        self.geom_start: QgsGeometry = None
        self.geom_end: QgsGeometry = None
        self.densify_distance = None
        self.fields = None
        self.transform = None
        self.polygon_source = polygon_source
        self.polygon_layer = self.map_manager.get_db_item_layer(self.project.map_guid, self.polygon_source, None).layer()
        Settings().iface.setActiveLayer(self.polygon_layer)
        Settings().iface.mapCanvas().selectionChanged.connect(self.capture_polygon)

        self.txtLayer.setText(self.polygon_source.name)
        self.capture_polygon()  # This should get the selection, if there are selected features in the polygon layer already
        self.txtStart.setText("")
        self.txtEnd.setText("")

        self.polygon_crs = self.polygon_layer.crs()
        canvas_crs = QgsCoordinateReferenceSystem(Settings().iface.mapCanvas().mapSettings().destinationCrs().authid())
        self.transform = QgsCoordinateTransform(canvas_crs, self.polygon_crs, QgsProject.instance().transformContext())

        self.d.setSourceCrs(self.polygon_crs, QgsProject.instance().transformContext())

        # Set up the Preview Layers in the polygon CRS. The start/end lines
        # are stored in polygon_crs, and QGIS on-the-fly reprojection handles
        # the UTM centerline display when we transform it for preview.
        self.remove_preview_layers()
        Settings().iface.mapCanvas().refresh()
        layer_uri = f"linestring?crs={self.polygon_crs.authid()}"

        self.layer_centerline = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_CENTERTLINE_MACHINE_CODE, "QRIS Centerline Preview", symbology_key="centerlines_temp", driver="memory")
        self.layer_start_line = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_STARTLINE_MACHINE_CODE, "QRIS Centerline Start Preview", driver="memory")
        self.layer_end_line = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_ENDLINE_MACHINE_CODE, "QRIS Centerline End Preview", driver="memory")

        # Set the symbology of the preview layers
        self.layer_start_line.renderer().symbol().symbolLayer(0).setColor(QColor("red"))
        self.layer_end_line.renderer().symbol().symbolLayer(0).setColor(QColor("red"))

        self.layer_centerline.triggerRepaint()
        self.layer_start_line.triggerRepaint()
        self.layer_end_line.triggerRepaint()
        Settings().iface.mapCanvas().refresh()

        # self.cmdSelectPolygon_click()

    def remove_preview_layers(self):
        for machine_code in [PREVIEW_STARTLINE_MACHINE_CODE, PREVIEW_CENTERTLINE_MACHINE_CODE, PREVIEW_ENDLINE_MACHINE_CODE]:
            self.map_manager.remove_machine_code_layer(self.project.map_guid, machine_code)

    def cmdSelectLayer_click(self):

        sv_layers = list(sv for sv in self.project.scratch_vectors.values() if QgsVectorLayer(f"{sv.gpkg_path}|layername={sv.fc_name}").geometryType() == Layer.GEOMETRY_TYPES["Polygon"])
        aoi_layers = list(layer for layer in self.project.aois.values())
        valley_bottom_layers = list(layer for layer in self.project.valley_bottoms.values())
        layers = sv_layers + aoi_layers + valley_bottom_layers
        frm_layer_picker = FrmLayerPicker(self, "Select Polygon Layer", layers)
        result = frm_layer_picker.exec()

        if result == DLG_ACCEPTED:
            self.centerline_setup(frm_layer_picker.layer)
        return

    def cmdSelectPolygon_click(self):
        Settings().iface.setActiveLayer(self.polygon_layer)
        Settings().iface.mapCanvas().selectionChanged.connect(self.capture_polygon)
        self.action = Settings().iface.actionSelect()
        self.action.trigger()

    def cmdCaptureStart_click(self):
        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Select one and only one polygon feature before capturing the starting/ending locations.")
            return
        self.layer_start_line.dataProvider().truncate()
        Settings().iface.mapCanvas().setMapTool(self.get_startline)

    def cmdCaptureEnd_click(self):
        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Select one and only one polygon feature before capturing the starting/ending locations.")
            return
        self.layer_end_line.dataProvider().truncate()
        Settings().iface.mapCanvas().setMapTool(self.get_endline)

    def cmdGenerateCl_click(self):

        if self.geom_polygon is None:
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Select one and only one polygon feature before generating centerline.")
            return
        if self.geom_start is None or self.geom_end is None:
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Capture the start and end of the polygon before generating centerline.")
            return
        if not all([self.geom_polygon.intersects(QgsGeometry().fromPolyline(self.geom_start)), self.geom_polygon.intersects(QgsGeometry().fromPolyline(self.geom_end))]):
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Make sure both start and stop lines intersect the polygon.")
            return
        if not self.geom_polygon.isGeosValid():
            QtWidgets.QMessageBox.information(self, "Centerline Tool", "The polygon geometry is not valid. Please fix and validate the polygon before generating centerline.")
            return

        self.layer_centerline.dataProvider().truncate()

        if self.geom_polygon.isMultipart():
            geom_polygon = QgsGeometry.fromMultiPolygonXY(self.geom_polygon.asMultiPolygon())
        else:
            geom_polygon = QgsGeometry.fromPolygonXY(self.geom_polygon.asPolygon())
        geom_start = self.geom_start.clone()
        geom_end = self.geom_end.clone()

        # The dial value is in meters. If the source CRS is geographic, transform
        # the inputs to UTM on the main thread so the task can use meter math.
        if self.polygon_crs.isGeographic():
            utm_crs = get_utm_crs(geom_polygon)
            xform = QgsCoordinateTransform(self.polygon_crs, utm_crs, QgsProject.instance().transformContext())
            geom_polygon.transform(xform)
            geom_start.transform(xform)
            geom_end.transform(xform)

        self.densify_distance = self.dblDensity.value()

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

    def cmdSaveCenterline_click(self):

        if self.feat_centerline is None:
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Generate the centerline before saving.")
            return

        # Use the original centerline geometry (in UTM for geographic sources,
        # or polygon CRS for already-projected sources).
        geom_centerline = QgsGeometry(self.geom_centerline)
        if geom_centerline.isMultipart():
            QtWidgets.QMessageBox.information(self, "Centerlines Error", "Unable to save a multipart centerline.")
            return

        # Transform to EPSG:4326 (the QRiS storage CRS) before saving to the GPKG.
        if self.polygon_crs.isGeographic():
            src_crs = get_utm_crs(self.geom_polygon)
        else:
            src_crs = self.polygon_crs
        transform = QgsCoordinateTransform(src_crs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance().transformContext())
        geom_centerline.transform(transform)

        sline_length = self.d.measureLine(QgsPointXY(geom_centerline.get().points()[0]), QgsPointXY(geom_centerline.get().points()[-1]))
        geom_length = self.d.measureLength(geom_centerline)
        metrics = {"total_length": geom_length, "sinuosity": geom_length / sline_length}

        temp_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "centerline", "memory")
        feat = QgsFeature()
        feat.setGeometry(geom_centerline)
        temp_layer.dataProvider().addFeatures([feat])

        frm_profile = FrmProfile(self, self.project, temp_layer, profile_type=Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE, fc_name="profile_centerlines", system_metadata=self.fields, metrics=metrics)
        result = frm_profile.exec()

        if result == DLG_ACCEPTED:
            self.centerline_setup(self.polygon_source)  # Reset the map
            self.export_complete.emit(frm_profile.profile, True)
        return

    def cmdReset_click(self):
        self.centerline_setup(self.polygon_source)
        return

    @pyqtSlot()
    def capture_polygon(self):
        # Defensive: check if the layer is still valid
        polygon_layer = self.map_manager.get_db_item_layer(self.project.map_guid, self.polygon_source, None).layer()
        if not polygon_layer or not QgsProject.instance().mapLayer(polygon_layer.id()):
            self.geom_polygon = None
            self.txtPolygon.setText("Polygon layer is missing or has been deleted")
            return

        features = polygon_layer.selectedFeatures()

        if len(features) == 1:
            self.geom_polygon = features[0].geometry()
            self.txtPolygon.setText(f"FeatureID: {features[0].id()}")
        elif len(features) == 0:
            self.geom_polygon = None
            self.txtPolygon.setText("No Features Selected")
        else:
            self.geom_polygon = None
            self.txtPolygon.setText("Multiple Features Selected")

    @pyqtSlot(QgsLineString)
    def capture_start(self, line_string):
        self.geom_start = line_string
        self.geom_start.transform(self.transform)
        self.txtStart.setText(self.geom_start.asWkt())
        self.txtStart.setCursorPosition(0)
        feat = QgsFeature()
        feat.setGeometry(self.geom_start)
        self.layer_start_line.dataProvider().addFeature(feat)
        self.layer_start_line.commitChanges()
        self.layer_start_line.triggerRepaint()
        Settings().iface.mapCanvas().unsetMapTool(self.get_startline)

    @pyqtSlot(QgsLineString)
    def capture_end(self, line_string):
        self.geom_end = line_string
        self.geom_end.transform(self.transform)
        self.txtEnd.setText(self.geom_end.asWkt())
        self.txtEnd.setCursorPosition(0)
        feat = QgsFeature()
        feat.setGeometry(self.geom_end)
        self.layer_end_line.dataProvider().addFeature(feat)
        self.layer_end_line.commitChanges()
        self.layer_end_line.triggerRepaint()
        Settings().iface.mapCanvas().unsetMapTool(self.get_endline)

    @pyqtSlot(QgsGeometry)
    def centerline_complete(self, centerline):

        geom_centerline_raw = QgsGeometry(centerline)
        smoothing_iter = self.dblSmoothingIter.value()
        # The centerline is in a projected CRS (UTM if the polygon CRS was
        # geographic), so distances are in meters and the dial is used directly.
        smoothing_dist = self.dblSmoothingMin.value()
        smoothing_offset = self.dblSmoothingOffset.value()
        smoothing_angle = self.dblSmoothingAngle.value()

        if smoothing_iter == 0:
            self.geom_centerline = QgsGeometry(geom_centerline_raw)
        else:
            self.geom_centerline = QgsGeometry(geom_centerline_raw.smooth(smoothing_iter, smoothing_offset, smoothing_dist, smoothing_angle))

        # The merged centerline can still be multi-part (disconnected fragments
        # from the boundary clip). Concatenate all parts into one polyline so
        # orientation works and the preview/save see a single line.
        cl_pts = []
        for part in self.geom_centerline.get().parts():
            cl_pts.extend(part.points())
        if not cl_pts:
            Settings.log("Centerline task produced an empty centerline", MESSAGE_LEVEL_CRITICAL)
            return
        self.geom_centerline = QgsGeometry(QgsLineString(cl_pts))

        # Orient so vertex[0] is at the start clip line (upstream end).
        # The returned centerline is in UTM (if the polygon CRS was geographic)
        # or the polygon CRS if it was already projected, so transform the start
        # clip line into that same CRS for the comparison.
        if self.polygon_crs.isGeographic():
            out_crs = get_utm_crs(self.geom_polygon)
        else:
            out_crs = self.polygon_crs
        transform = QgsCoordinateTransform(self.polygon_crs, out_crs, QgsProject.instance().transformContext())

        start_pts = self.geom_start.points()
        start_mid = QgsGeometry.fromPointXY(QgsPointXY((start_pts[0].x() + start_pts[-1].x()) / 2.0, (start_pts[0].y() + start_pts[-1].y()) / 2.0))
        start_mid.transform(transform)

        cl_pts = self.geom_centerline.get().points()
        if QgsGeometry.fromPointXY(QgsPointXY(cl_pts[-1])).distance(start_mid) < QgsGeometry.fromPointXY(QgsPointXY(cl_pts[0])).distance(start_mid):
            self.geom_centerline = QgsGeometry(QgsLineString(list(reversed(cl_pts))))

        self.feat_centerline = QgsFeature()

        # The centerline is in UTM for geographic sources, but the preview
        # layer is in polygon_crs. Transform a copy for display.
        if self.polygon_crs.isGeographic():
            out_crs = get_utm_crs(self.geom_polygon)
            preview_transform = QgsCoordinateTransform(out_crs, self.polygon_crs, QgsProject.instance().transformContext())
            geom_preview = QgsGeometry(self.geom_centerline)
            geom_preview.transform(preview_transform)
        else:
            geom_preview = QgsGeometry(self.geom_centerline)
        self.feat_centerline.setGeometry(geom_preview)

        self.fields = {
            "parent_polygon_type": self.polygon_source.db_table_name,
            "parent_polygon_id": self.polygon_source.id,
            "parent_polygon_fid": self.txtPolygon.text(),
            "start_line": self.geom_start.asWkt(),
            "end_line": self.geom_start.asWkt(),
            "densify_distance": self.densify_distance,
            "smoothing_iterations": smoothing_iter,
            "smoothing_offset": smoothing_offset,
            "smoothing_min_distance": smoothing_dist,
            "smoothing_max_angle": smoothing_angle,
        }

        self.layer_centerline.dataProvider().addFeature(self.feat_centerline)
        self.layer_centerline.commitChanges()
        self.layer_centerline.triggerRepaint()
        Settings().iface.mapCanvas().refresh()

    def closeEvent(self, event):
        self.remove_preview_layers()
        QtWidgets.QDockWidget.closeEvent(self, event)

    def setupUi(self):

        self.setWindowTitle("Generate Centerlines")

        self.dockWidgetContents = QtWidgets.QWidget(self)
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        self.tabCenterline = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tabCenterline, "Centerline Inputs")

        self.gridCenterline = QtWidgets.QGridLayout()
        self.tabCenterline.setLayout(self.gridCenterline)

        self.lblLayer = QtWidgets.QLabel("Polygon Layer")
        self.gridCenterline.addWidget(self.lblLayer, 0, 0, 1, 1)

        self.horizLayer = QtWidgets.QHBoxLayout()
        self.gridCenterline.addLayout(self.horizLayer, 0, 1, 1, 1)

        self.txtLayer = QtWidgets.QLineEdit()
        self.txtLayer.setReadOnly(True)
        self.horizLayer.addWidget(self.txtLayer)

        self.cmdSelectLayer = QtWidgets.QPushButton("Select")
        self.cmdSelectLayer.setToolTip("Select Polygon Layer")
        self.cmdSelectLayer.clicked.connect(self.cmdSelectLayer_click)
        self.horizLayer.addWidget(self.cmdSelectLayer)

        self.lblPolygon = QtWidgets.QLabel("Polygon Feature")
        self.gridCenterline.addWidget(self.lblPolygon, 1, 0, 1, 1)

        self.horizPoly = QtWidgets.QHBoxLayout()
        self.gridCenterline.addLayout(self.horizPoly, 1, 1, 1, 1)

        self.txtPolygon = QtWidgets.QLineEdit()
        self.txtPolygon.setReadOnly(True)
        self.horizPoly.addWidget(self.txtPolygon)

        self.cmdPolygon = QtWidgets.QPushButton("Select")
        self.cmdPolygon.setToolTip("Select Polygon on map")
        self.cmdPolygon.clicked.connect(self.cmdSelectPolygon_click)
        self.horizPoly.addWidget(self.cmdPolygon)

        self.lblStart = QtWidgets.QLabel("Start of Centerline")
        self.gridCenterline.addWidget(self.lblStart, 2, 0, 1, 1)

        self.horizStart = QtWidgets.QHBoxLayout()
        self.gridCenterline.addLayout(self.horizStart, 2, 1, 1, 1)

        self.txtStart = QtWidgets.QLineEdit()
        self.txtStart.setReadOnly(True)
        self.horizStart.addWidget(self.txtStart)

        self.cmdCaptureS = QtWidgets.QPushButton("Capture")
        self.cmdCaptureS.setToolTip("Manually capture the transect across the polygon at the start of the centerline.\n\n Start and end the transect outside of the polygon, only crossing the polygon once.")
        self.cmdCaptureS.clicked.connect(self.cmdCaptureStart_click)
        self.horizStart.addWidget(self.cmdCaptureS)

        self.lblEnd = QtWidgets.QLabel("End of Centerline")
        self.gridCenterline.addWidget(self.lblEnd, 3, 0, 1, 1)

        self.horizEnd = QtWidgets.QHBoxLayout()
        self.gridCenterline.addLayout(self.horizEnd, 3, 1, 1, 1)

        self.txtEnd = QtWidgets.QLineEdit()
        self.txtEnd.setReadOnly(True)
        self.horizEnd.addWidget(self.txtEnd)

        self.cmdCaptureE = QtWidgets.QPushButton("Capture")
        self.cmdCaptureE.setToolTip("Manually capture the transect across the polygon at the end of the centerline.\n\n Start and end the transect outside of the polygon, only crossing the polygon once.")
        self.cmdCaptureE.clicked.connect(self.cmdCaptureEnd_click)
        self.horizEnd.addWidget(self.cmdCaptureE)

        self.cmdReset = QtWidgets.QPushButton("Reset")
        self.cmdReset.setToolTip("Reset the centerline tool polygon, transects, and parameters")
        self.cmdReset.setFixedSize(self.cmdReset.sizeHint())
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.gridCenterline.addWidget(self.cmdReset, 4, 0, 1, 1)

        # add tab for the smoothing parameters
        self.tabSmoothing = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tabSmoothing, "Smoothing")

        self.gridSmoothing = QtWidgets.QGridLayout()
        self.tabSmoothing.setLayout(self.gridSmoothing)

        self.lblDensity = QtWidgets.QLabel("Polygon Densify Dist.")
        self.lblDensity.setToolTip("Densify the polygon by adding regularly placed extra nodes inside each segment so that the maximum distance between any two nodes does not exceed the specified distance")
        self.gridSmoothing.addWidget(self.lblDensity, 0, 0, 1, 1)

        self.dblDensity = QtWidgets.QSpinBox()
        self.dblDensity.setValue(10)
        self.dblDensity.setSuffix(" m")
        self.dblDensity.setRange(0, 500)
        self.gridSmoothing.addWidget(self.dblDensity, 0, 1, 1, 1)

        self.lblSmoothingIter = QtWidgets.QLabel("Smoothing Iterations")
        self.lblSmoothingIter.setToolTip("number of smoothing iterations to run. More iterations results in a smoother geometry, but produces more vertices. Set to 0 for no smoothing.")
        self.gridSmoothing.addWidget(self.lblSmoothingIter, 1, 0, 1, 1)

        self.dblSmoothingIter = QtWidgets.QSpinBox()
        self.dblSmoothingIter.setValue(1)
        self.dblSmoothingIter.setRange(0, 5)
        self.gridSmoothing.addWidget(self.dblSmoothingIter, 1, 1, 1, 1)

        self.lblSmoothingOffset = QtWidgets.QLabel("Smoothing Offset")
        self.lblSmoothingOffset.setToolTip(
            r"fraction of line to create new vertices along, between 0 and 1.0, e.g., the default value of 0.5 will create new vertices 50% along the distance of each line segment of the geometry for each iteration."
            "Smaller values result in “tighter” smoothing."
        )
        self.gridSmoothing.addWidget(self.lblSmoothingOffset, 2, 0, 1, 1)

        self.dblSmoothingOffset = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingOffset.setDecimals(2)
        self.dblSmoothingOffset.setValue(0.5)
        self.dblSmoothingOffset.setSingleStep(0.05)
        self.dblSmoothingOffset.setRange(0, 1)
        self.gridSmoothing.addWidget(self.dblSmoothingOffset, 2, 1, 1, 1)

        self.lblSmoothingMin = QtWidgets.QLabel("Smoothing Min Distance")
        self.lblSmoothingMin.setToolTip("minimum segment length to apply smoothing to")
        self.gridSmoothing.addWidget(self.lblSmoothingMin, 3, 0, 1, 1)

        self.dblSmoothingMin = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingMin.setSuffix(" m")
        self.dblSmoothingMin.setDecimals(1)
        self.dblSmoothingMin.setRange(-1.0, 500.0)
        self.dblSmoothingMin.setValue(-1.0)
        self.dblSmoothingMin.setSingleStep(5)
        self.gridSmoothing.addWidget(self.dblSmoothingMin, 3, 1, 1, 1)

        self.lblSmoothingAngle = QtWidgets.QLabel("Smoothing Max Angle")
        self.lblSmoothingAngle.setToolTip("maximum angle at node (0-180) at which smoothing will be applied")
        self.gridSmoothing.addWidget(self.lblSmoothingAngle, 4, 0, 1, 1)

        self.dblSmoothingAngle = QtWidgets.QDoubleSpinBox()
        self.dblSmoothingAngle.setSuffix(" degrees")
        self.dblSmoothingAngle.setDecimals(1)
        self.dblSmoothingAngle.setRange(0, 180)
        self.dblSmoothingAngle.setValue(180.0)
        self.gridSmoothing.addWidget(self.dblSmoothingAngle, 4, 1, 1, 1)

        # Turn off the smoothing angle for now, as it is not currently used in the smoothing algorithm
        self.lblSmoothingAngle.setVisible(False)
        self.dblSmoothingAngle.setVisible(False)

        # add grid for the buttons
        self.gridButtons = QtWidgets.QGridLayout()
        self.vert.addLayout(self.gridButtons)

        self.gridButtons.addWidget(add_help_button(self, "inputs/valley-bottoms#centerline-tool"), 0, 0, 1, 1)

        # include a spacer to push the buttons to the right
        self.gridButtons.addItem(QtWidgets.QSpacerItem(0, 0, SPSZ_EXPANDING, SPSZ_MINIMUM), 0, 1, 1, 1)

        self.cmdGenerateCl = QtWidgets.QPushButton("Generate Centerline")
        self.cmdGenerateCl.setToolTip("Generate a preview the centerline")
        self.cmdGenerateCl.clicked.connect(self.cmdGenerateCl_click)
        self.gridButtons.addWidget(self.cmdGenerateCl, 0, 2, 1, 1)

        self.cmdSaveCl = QtWidgets.QPushButton("Save Centerline")
        self.cmdSaveCl.setToolTip("Save the centerline to the project")
        self.cmdSaveCl.clicked.connect(self.cmdSaveCenterline_click)
        self.gridButtons.addWidget(self.cmdSaveCl, 1, 2, 1, 1)

        self.setWidget(self.dockWidgetContents)
