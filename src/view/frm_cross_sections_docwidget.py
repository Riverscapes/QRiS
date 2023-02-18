"""
Doc Widget for building x-sections from centerlines

"""

from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature, QgsDistanceArea
from qgis.utils import iface

from ..gp.cross_sections import CrossSectionsTask
from ..model.project import Project
from ..model.profile import Profile
from ..model.cross_sections import CrossSections
from .utilities import add_help_button
from .frm_cross_sections import FrmCrossSections
from ..QRiS.qris_map_manager import QRisMapManager

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

        self.cross_sections_setup()

    def cross_sections_setup(self):

        self.xsections = None
        self.geom_centerline = None

        self.txtProfile.setText(self.profile.name)

        self.remove_preview_layers()
        iface.mapCanvas().refresh()

        layer_uri = f'linestring'

        self.layer_preview_cl = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_XS_CENTERLINE_MACHINE_CODE, "QRIS XS Centerline Preview", driver='memory')
        self.layer_preview_xs = self.map_manager.create_temporary_feature_layer(self.project.map_guid, layer_uri, PREVIEW_CROSS_SECTIONS_MACHINE_CODE, "QRIS Cross Section Preview", driver='memory')

        self.layer_preview_cl.renderer().symbol().symbolLayer(0).setColor(QColor('darkblue'))
        self.layer_preview_cl.renderer().symbol().symbolLayer(0).setWidth(0.66)
        self.layer_preview_xs.renderer().symbol().symbolLayer(0).setColor(QColor('cornflowerblue'))

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
        iface.mapCanvas().refresh()

    def remove_preview_layers(self):
        for machine_code in [PREVIEW_CROSS_SECTIONS_MACHINE_CODE, PREVIEW_XS_CENTERLINE_MACHINE_CODE]:
            self.map_manager.remove_machine_code_layer(self.project.map_guid, machine_code)

    def cmdGenerateXS_click(self):

        if self.geom_centerline is None:
            QtWidgets.QMessageBox.information(self, 'Cross Sections Error', 'Load centerline before generating cross sections.')
            return

        offset = (self.dblOffset.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        spacing = (self.dblSpacing.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()
        extension = (self.dblExtension.value() / self.d.measureLength(self.geom_centerline)) * self.geom_centerline.length()

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

        metadata = {
            'parent_profile_source': self.profile.db_table_name,
            'parent_profile_id': self.profile.id,
            # 'clipping_polygon_source': self.clip_polygon,
            # 'clipping_polygon_id':,
            # 'clipping_polygon_fid':,
            'offset': self.dblOffset.value(),
            'spacing': self.dblSpacing.value(),
            'extension': self.dblExtension.value()
        }

        frm_x_sections = FrmCrossSections(self, self.project, output_features=self.xsections)

        frm_x_sections.add_metadata(metadata)
        result = frm_x_sections.exec_()

        if result == QtWidgets.QDialog.Accepted:
            self.cross_sections_setup()  # Reset the map
            self.export_complete.emit(frm_x_sections.cross_sections, CrossSections.CROSS_SECTIONS_MACHINE_CODE, True, True)
        return

    def cmdReset_click(self):
        self.cross_sections_setup()
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

        self.setWindowTitle("Build Cross Sections")

        self.dockWidgetContents = QtWidgets.QWidget()
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblLayer = QtWidgets.QLabel('Profile')
        self.grid.addWidget(self.lblLayer, 0, 0, 1, 1)

        self.txtProfile = QtWidgets.QLineEdit()
        self.txtProfile.setReadOnly(True)
        self.grid.addWidget(self.txtProfile, 0, 1, 1, 1)

        self.lblOffset = QtWidgets.QLabel('Offset (m)')
        self.lblOffset.setVisible(False)
        self.grid.addWidget(self.lblOffset, 4, 0, 1, 1)

        self.dblOffset = QtWidgets.QDoubleSpinBox()
        self.dblOffset.setDecimals(1)
        self.dblOffset.setValue(10)
        self.dblOffset.setRange(0, 500)
        self.dblOffset.setVisible(False)
        self.grid.addWidget(self.dblOffset, 4, 1, 1, 1)

        self.lblSpacing = QtWidgets.QLabel('Spacing (m)')
        self.grid.addWidget(self.lblSpacing, 5, 0, 1, 1)

        self.dblSpacing = QtWidgets.QDoubleSpinBox()
        self.dblSpacing.setDecimals(1)
        self.dblSpacing.setValue(10)
        self.dblSpacing.setRange(0, 500)
        self.grid.addWidget(self.dblSpacing, 5, 1, 1, 1)

        self.lblExtension = QtWidgets.QLabel('Extension (m)')
        self.grid.addWidget(self.lblExtension, 6, 0, 1, 1)

        self.dblExtension = QtWidgets.QDoubleSpinBox()
        self.dblExtension.setDecimals(1)
        self.dblExtension.setValue(10)
        self.dblExtension.setRange(0, 500)
        self.grid.addWidget(self.dblExtension, 6, 1, 1, 1)

        self.horizBottom = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizBottom, 8, 1, 1, 1)

        self.cmdGenerateXS = QtWidgets.QPushButton('Generate')
        self.cmdGenerateXS.clicked.connect(self.cmdGenerateXS_click)
        self.horizBottom.addWidget(self.cmdGenerateXS)

        self.cmdExportXS = QtWidgets.QPushButton('Export')
        self.cmdExportXS.clicked.connect(self.cmdExportXS_click)
        self.horizBottom.addWidget(self.cmdExportXS)

        self.cmdReset = QtWidgets.QPushButton('Reset')
        self.cmdReset.clicked.connect(self.cmdReset_click)
        self.grid.addWidget(self.cmdReset, 7, 0, 1, 1)

        self.vert.addLayout(add_help_button(self, 'cross_sections'))

        self.setWidget(self.dockWidgetContents)
