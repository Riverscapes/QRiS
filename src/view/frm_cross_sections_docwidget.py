"""
Doc Widget for building x-sections from centerlines

"""
import sqlite3

from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsProject, QgsLineString, QgsVectorLayer, QgsFeature, QgsGeometry, QgsMapLayer, QgsDistanceArea, QgsPointXY
from qgis.gui import QgsMapToolIdentifyFeature

from ..gp.cross_sections import CrossSectionsTask
from ..model.project import Project
from .utilities import add_help_button
from .frm_save_centerline import FrmSaveCenterline


class FrmCrossSectionsDocWidget(QtWidgets.QDockWidget):

    def __init__(self, parent, project: Project, iface):

        super(FrmCrossSectionsDocWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi()

        self.project = project
        self.iface = iface
        self.parent = parent
        self.canvas = self.iface.mapCanvas()

        self.polygon_layer = None
        self.layer_preview_cl = None
        self.layer_preview_xs = None

        self.xsections = None

        self.d = QgsDistanceArea()
        self.d.setEllipsoid('WGS84')

        self.cross_sections_setup()

        self.cmbCenterline.currentIndexChanged.connect(self.on_centerline_change)

    def cross_sections_setup(self):

        self.feat_centerline = None
        self.geom_centerline = None
        self.geom_polygon = None
        self.layer_centerlines = QgsVectorLayer(f'{self.project.project_file}|layername=centerlines')

        self.txtPolygon.setText("")

        self.remove_cl_temp_layers()
        self.canvas.refresh()

        self.layer_preview_cl = QgsVectorLayer('linestring', "QRIS XSections Centerline Preview", 'memory')
        self.layer_preview_xs = QgsVectorLayer('linestring', "QRIS XSections Preview", 'memory')
        # self.layer_end_line = QgsVectorLayer('linestring', "QRIS Centerline End Preview", 'memory')

        self.layer_preview_cl.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
        self.layer_preview_xs.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
        # self.layer_end_line.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))

        self.layer_preview_cl.renderer().symbol().symbolLayer(0).setColor(QColor('darkblue'))
        self.layer_preview_cl.renderer().symbol().symbolLayer(0).setWidth(0.66)
        self.layer_preview_xs.renderer().symbol().symbolLayer(0).setColor(QColor('cornflowerblue'))
        # self.layer_end_line.renderer().symbol().symbolLayer(0).setColor(QColor('red'))

        QgsProject.instance().addMapLayers([self.layer_preview_cl, self.layer_preview_xs])

    def configure_polygon(self, polygon_layer):

        self.polygon_layer = polygon_layer
        self.txtLayer.setText(polygon_layer.name)
        fc_path = f'{polygon_layer.gpkg_path}|layername={polygon_layer.fc_name}'

        # TODO Filter by polygons that have associated centerlines?

        # Initially choose first feature here
        layer = QgsVectorLayer(fc_path, polygon_layer.fc_name, 'ogr')
        feats = layer.getFeatures()
        feat = QgsFeature()
        feats.nextFeature(feat)
        self.geom_polygon = feat.geometry()
        self.txtPolygon.setText(f'FeatureID: {feat.id()}')

        self.on_polygon_change()

    def on_polygon_change(self):

        # Load Centerlines by name to combo box
        feats = self.layer_centerlines.getFeatures()  # TODO set selection to polygon refrence only QgsFeatureRequest().setFilter()
        for feat in feats:
            self.cmbCenterline.addItem(f"FeatureID: {feat['fid']}", feat.geometry())  # TODO fetch centerline name. need to write it to database first

    def on_centerline_change(self):

        self.layer_preview_cl.dataProvider().truncate()
        self.geom_centerline = self.cmbCenterline.currentData()
        feat = QgsFeature()
        feat.setGeometry(self.geom_centerline)
        self.layer_preview_cl.dataProvider().addFeature(feat)
        self.layer_preview_cl.commitChanges()
        self.canvas.refreshAllLayers()

        return

    def remove_cl_temp_layers(self):
        map_layers = QgsProject.instance().mapLayers()
        for layer in map_layers:
            if map_layers[layer].name() in ["QRIS XSections Centerline Preview", "QRIS XSections Preview"]:
                QgsProject.instance().removeMapLayer(map_layers[layer].id())

    def cmdSelect_click(self):
        layers = QgsProject.instance().mapLayersByName(self.polygon_layer.name)
        layer = layers[0]
        self.get_polygon = QgsMapToolIdentifyFeature(self.canvas, layer)
        self.canvas.setMapTool(self.get_polygon)
        self.get_polygon.featureIdentified.connect(self.capture_polygon)

    def cmdGenerateXS_click(self):

        if self.geom_polygon is None and self.geom_centerline is None:
            QtWidgets.QMessageBox.information(self, 'Cross Sections Error', 'Load the polygon and centerline before generating cross sections.')
            return

        offset = (self.dblOffset.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        spacing = (self.dblSpacing.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        extension = (self.dblExtension.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()

        xsections_task = CrossSectionsTask(self.geom_polygon, self.geom_centerline, offset, spacing, extension)
        # DEBUG
        xsections_task.run()
        self.cross_sections_complete(xsections_task.xsections)
        # PRODUCTION
        # centerline_task.centerline_complete.connect(self.centerline_complete)
        # QgsApplication.taskManager().addTask(centerline_task)

        return

    def cmdExportXS_click(self):

        if self.xsections is None:
            QtWidgets.QMessageBox.information(self, 'Cross Sections Error', 'Generate the cross sections before saving.')
            return

        QtWidgets.QMessageBox.information(self, 'Not Implemented', 'Export cross sections not yet implemented.')
        return

        # sline_length = self.d.measureLine(QgsPointXY(self.geom_centerline.get().points()[0]), QgsPointXY(self.geom_centerline.get().points()[-1]))
        # geom_length = self.d.measureLength(self.geom_centerline)
        # metrics = {'Length (m)': geom_length, 'Sinuosity': geom_length / sline_length}
        # frm_save_centerline = FrmSaveCenterline(self.parent, self.iface, self.project)
        # frm_save_centerline.add_metrics(metrics)

        # frm_save_centerline.add_centerline(self.feat_centerline)
        # result = frm_save_centerline.exec_()

        # TODO add to map

        # self.cross_sections_setup()  # Reset the map
        # return

    def cmdReset_click(self):
        self.cross_sections_setup()
        return

    @ pyqtSlot(QgsFeature)
    def capture_polygon(self, selected_polygon_feature):

        self.geom_polygon = selected_polygon_feature.geometry()
        self.txtPolygon.setText(f'FeatureID: {selected_polygon_feature.id()}')
        self.canvas.unsetMapTool(self.get_polygon)
        self.get_polygon = None

    @ pyqtSlot(list)
    def cross_sections_complete(self, xsections):

        self.layer_preview_xs.dataProvider().truncate()
        self.xsections = xsections
        self.layer_preview_xs.dataProvider().addFeatures(self.xsections)
        self.layer_preview_xs.commitChanges()
        self.canvas.refreshAllLayers()

    def setupUi(self):

        self.setWindowTitle("Build Cross Sections")

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

        self.lblCenterline = QtWidgets.QLabel()
        self.lblCenterline.setText('Centerline')
        self.grid.addWidget(self.lblCenterline, 2, 0, 1, 1)

        self.horizCL = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizCL, 2, 1, 1, 1)

        self.cmbCenterline = QtWidgets.QComboBox()
        self.horizCL.addWidget(self.cmbCenterline)

        self.lblOffset = QtWidgets.QLabel()
        self.lblOffset.setText('Offset (m)')
        self.grid.addWidget(self.lblOffset, 4, 0, 1, 1)

        self.dblOffset = QtWidgets.QDoubleSpinBox()
        self.dblOffset.setDecimals(1)
        self.dblOffset.setValue(10)
        self.dblOffset.setRange(0, 500)
        self.grid.addWidget(self.dblOffset, 4, 1, 1, 1)

        self.lblSpacing = QtWidgets.QLabel()
        self.lblSpacing.setText('Spacing (m)')
        self.grid.addWidget(self.lblSpacing, 5, 0, 1, 1)

        self.dblSpacing = QtWidgets.QDoubleSpinBox()
        self.dblSpacing.setDecimals(1)
        self.dblSpacing.setValue(10)
        self.dblSpacing.setRange(0, 500)
        self.grid.addWidget(self.dblSpacing, 5, 1, 1, 1)

        self.lblExtension = QtWidgets.QLabel()
        self.lblExtension.setText('Extension (m)')
        self.grid.addWidget(self.lblExtension, 6, 0, 1, 1)

        self.dblExtension = QtWidgets.QDoubleSpinBox()
        self.dblExtension.setDecimals(1)
        self.dblExtension.setValue(10)
        self.dblExtension.setRange(0, 500)
        self.grid.addWidget(self.dblExtension, 6, 1, 1, 1)

        self.horizBottom = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizBottom, 8, 1, 1, 1)

        self.cmdGenerateXS = QtWidgets.QPushButton()
        self.cmdGenerateXS.setText('Generate')
        self.cmdGenerateXS.clicked.connect(self.cmdGenerateXS_click)
        self.horizBottom.addWidget(self.cmdGenerateXS)

        self.cmdExportXS = QtWidgets.QPushButton()
        self.cmdExportXS.setText('Export')
        self.cmdExportXS.clicked.connect(self.cmdExportXS_click)
        self.horizBottom.addWidget(self.cmdExportXS)

        self.cmdReset = QtWidgets.QPushButton()
        self.cmdReset.setText('Reset')
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 7, 0, 1, 1)

        self.vert.addLayout(add_help_button(self, 'cross_sections'))

        self.setWidget(self.dockWidgetContents)
