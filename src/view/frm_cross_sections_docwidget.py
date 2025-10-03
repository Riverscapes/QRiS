"""
Doc Widget for building x-sections from centerlines

"""

from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCoordinateTransform, QgsDistanceArea
from qgis.utils import iface

from ..gp.cross_sections import CrossSectionsTask
from ..model.project import Project
from ..model.profile import Profile
from ..model.cross_sections import CrossSections
from ..QRiS.qris_map_manager import QRisMapManager
from .utilities import add_help_button
from .frm_cross_sections import FrmCrossSections
from .frm_layer_picker import FrmLayerPicker

PREVIEW_CROSS_SECTIONS_MACHINE_CODE = "Cross Section Preview"
PREVIEW_XS_CENTERLINE_MACHINE_CODE = "XS Centerline Preview"


class FrmCrossSectionsDocWidget(QtWidgets.QDockWidget):

    export_complete = pyqtSignal(CrossSections or None, str, bool, bool)

    def __init__(self, parent, project: Project, profile: Profile, map_manager: QRisMapManager):

        super(FrmCrossSectionsDocWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        self.setupUi()

        self.project = project
        self.profile = profile
        self.map_manager = map_manager

        self.d = QgsDistanceArea()
        self.d.setEllipsoid('WGS84')

        self.cross_sections_setup(profile)

    def cross_sections_setup(self, profile: Profile = None):

        self.profile = profile
        self.xsections = None
        self.geom_centerline = None

        self.remove_preview_layers()
        iface.mapCanvas().refresh()

        if self.profile is None:
            self.txtProfile.setText('')
            return

        self.txtProfile.setText(self.profile.name)

        layer_uri = f'linestring'

        self.layer_preview_cl = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_XS_CENTERLINE_MACHINE_CODE, "QRIS XS Centerline Preview", symbology_key='centerlines_temp', driver='memory')
        self.layer_preview_xs = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_CROSS_SECTIONS_MACHINE_CODE, "QRIS Cross Section Preview", symbology_key='cross_sections_temp', driver='memory')

        if self.profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE:
            layer_name = 'profile_centerlines'
        else:
            layer_name = 'profile_features'
        self.layer_centerlines = QgsVectorLayer(f'{self.project.project_file}|layername={layer_name}')
        self.layer_centerlines.setSubsetString(f'profile_id = {self.profile.id}')
        feats = self.layer_centerlines.getFeatures()
        feat = QgsFeature()
        feats.nextFeature(feat)
        self.geom_centerline = feat.geometry()
        temp_feat = QgsFeature()
        temp_feat.setGeometry(self.geom_centerline)
        self.layer_preview_cl.dataProvider().addFeature(temp_feat)
        self.layer_preview_cl.commitChanges()

        self.layer_preview_cl.triggerRepaint()
        self.layer_preview_xs.triggerRepaint()

        # get srs of profile layer
        srs = self.layer_centerlines.crs()
        extent = self.layer_centerlines.extent()
        # get srs of canvas
        canvas_srs = iface.mapCanvas().mapSettings().destinationCrs()
        # if srs of profile layer is not the same as canvas srs, transform extent
        if srs.authid() != canvas_srs.authid():
            transform = QgsCoordinateTransform(srs, canvas_srs, QgsProject.instance())
            geom = QgsGeometry.fromRect(extent)
            geom.transform(transform)
            # buffer by 10% to ensure all features are visible
            geom_buff = geom.buffer(geom.boundingBox().width() * 0.1, 1)
            extent = geom_buff.boundingBox()
        # zoom to extent
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()

    def remove_preview_layers(self):
        for machine_code in [PREVIEW_CROSS_SECTIONS_MACHINE_CODE, PREVIEW_XS_CENTERLINE_MACHINE_CODE]:
            self.map_manager.remove_machine_code_layer(self.project.map_guid, machine_code)

    def cmdLoadProfile_click(self):

        layers = list(layer for layer in self.project.profiles.values())
        frm_layer_picker = FrmLayerPicker(self, "Select Profile Layer", layers)
        result = frm_layer_picker.exec_()

        if result == QtWidgets.QDialog.Accepted:
            self.cross_sections_setup(frm_layer_picker.layer)
        return

    def cmdGenerateXS_click(self):

        if self.geom_centerline is None:
            QtWidgets.QMessageBox.information(self, 'Cross Sections Error', 'Load centerline before generating cross sections.')
            return

        offset = (self.dblOffset.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        spacing = (self.dblSpacing.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        extension = ((self.dblExtension.value() / 2) / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()

        cross_sections_task = CrossSectionsTask(self.geom_centerline, offset, spacing, extension, self.d)
        # -- DEBUG --
        # xsections_task.run()
        # self.cross_sections_complete(xsections_task.xsections)
        # -- PRODUCTION --
        cross_sections_task.cross_sections_complete.connect(self.cross_sections_complete)
        QgsApplication.taskManager().addTask(cross_sections_task)

        return

    def cmdExportXS_click(self):

        if self.xsections is None:
            QtWidgets.QMessageBox.information(self, 'Cross Sections Error', 'Generate the cross sections before saving.')
            return

        out_metadata = {
            'parent_profile_source': self.profile.db_table_name,
            'parent_profile_id': self.profile.id,
            # 'clipping_polygon_source': self.clip_polygon,
            # 'clipping_polygon_id':,
            # 'clipping_polygon_fid':,
            'offset': self.dblOffset.value(),
            'spacing': self.dblSpacing.value(),
            'extension': self.dblExtension.value()
        }

        frm_x_sections = FrmCrossSections(self, self.project, output_features=self.xsections, metadata=out_metadata)

        result = frm_x_sections.exec_()

        if result == QtWidgets.QDialog.Accepted:
            self.cross_sections_setup()  # Reset the map
            self.export_complete.emit(frm_x_sections.cross_sections, CrossSections.CROSS_SECTIONS_MACHINE_CODE, True, True)
        return

    def cmdReset_click(self):
        self.cross_sections_setup(self.profile)
        return

    @ pyqtSlot(dict)
    def cross_sections_complete(self, xsections):

        self.layer_preview_xs.dataProvider().truncate()
        self.xsections = xsections
        self.layer_preview_xs.dataProvider().addFeatures(list(self.xsections.values()))
        self.layer_preview_xs.commitChanges()
        self.layer_preview_xs.triggerRepaint()
        iface.mapCanvas().refresh()

    def closeEvent(self, event):
        self.remove_preview_layers()
        QtWidgets.QDockWidget.closeEvent(self, event)

    def setupUi(self):

        self.setWindowTitle("Generate Cross Sections")

        self.dockWidgetContents = QtWidgets.QWidget()
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.groupbox = QtWidgets.QGroupBox()
        self.groupbox.setTitle('Cross Section Inputs')
        self.groupbox.setStyleSheet("QGroupBox { border: 1px solid black;} QGroupBox::title {subcontrol-origin: margin; left: 10px; top: 10px;}")
        self.vert.addWidget(self.groupbox)

        self.grid = QtWidgets.QGridLayout(self.groupbox)
        self.groupbox.setLayout(self.grid)

        self.lblLayer = QtWidgets.QLabel('Profile')
        self.lblLayer.setToolTip('Profile (e.g. centerline) to generate cross sections from.')
        self.grid.addWidget(self.lblLayer, 0, 0, 1, 1)

        self.horizProfile = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizProfile, 0, 1, 1, 1)

        self.txtProfile = QtWidgets.QLineEdit()
        self.txtProfile.setReadOnly(True)
        self.horizProfile.addWidget(self.txtProfile)

        self.cmdLoadProfile = QtWidgets.QPushButton('Select')
        self.cmdLoadProfile.setToolTip('Select the profile to generate cross sections from.')
        self.cmdLoadProfile.clicked.connect(self.cmdLoadProfile_click)
        self.horizProfile.addWidget(self.cmdLoadProfile)

        self.lblOffset = QtWidgets.QLabel('Offset')
        self.lblOffset.setVisible(False)
        self.grid.addWidget(self.lblOffset, 4, 0, 1, 1)

        self.dblOffset = QtWidgets.QDoubleSpinBox()
        self.dblOffset.setDecimals(1)
        self.dblOffset.setValue(10)
        self.dblOffset.setSuffix(' m')
        self.dblOffset.setRange(0, 500)
        self.dblOffset.setVisible(False)
        self.grid.addWidget(self.dblOffset, 4, 1, 1, 1)

        self.lblSpacing = QtWidgets.QLabel('Spacing')
        self.lblSpacing.setToolTip('Distance between cross sections.')
        self.grid.addWidget(self.lblSpacing, 5, 0, 1, 1)

        self.dblSpacing = QtWidgets.QDoubleSpinBox()
        self.dblSpacing.setDecimals(1)
        self.dblSpacing.setValue(50.0)
        self.dblSpacing.setSuffix(' m')
        self.dblSpacing.setRange(0, 10000)
        self.grid.addWidget(self.dblSpacing, 5, 1, 1, 1)

        self.lblExtension = QtWidgets.QLabel('Length')
        self.lblExtension.setToolTip('Total length of each cross section.')
        self.grid.addWidget(self.lblExtension, 6, 0, 1, 1)

        self.dblExtension = QtWidgets.QDoubleSpinBox()
        self.dblExtension.setDecimals(1)
        self.dblExtension.setValue(25.0)
        self.dblExtension.setSuffix(' m')
        self.dblExtension.setRange(0.0, 5000.0)
        self.grid.addWidget(self.dblExtension, 6, 1, 1, 1)

        self.cmdReset = QtWidgets.QPushButton('Reset')
        self.cmdReset.setToolTip('Reset the cross sections tool')
        self.cmdReset.setFixedSize(self.cmdReset.sizeHint())
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 7, 0, 1, 1)

        self.gridButtons = QtWidgets.QGridLayout()
        self.vert.addLayout(self.gridButtons)

        self.gridButtons.addWidget(add_help_button(self, 'cross-sections'), 0, 0, 1, 1)

        self.cmdGenerateXS = QtWidgets.QPushButton('Generate Cross Sections')
        self.cmdGenerateXS.setToolTip('Generate a preview of the cross sections')
        self.cmdGenerateXS.clicked.connect(self.cmdGenerateXS_click)
        self.gridButtons.addWidget(self.cmdGenerateXS, 0, 2, 1, 1)

        self.gridButtons.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum), 0, 1, 1, 1)

        self.cmdExportXS = QtWidgets.QPushButton('Save Cross Sections')
        self.cmdExportXS.setToolTip('Save cross sections to the project, with an option to clip to a polygon mask')
        self.cmdExportXS.clicked.connect(self.cmdExportXS_click)
        self.gridButtons.addWidget(self.cmdExportXS, 1, 2, 1, 1)

        self.setWidget(self.dockWidgetContents)
