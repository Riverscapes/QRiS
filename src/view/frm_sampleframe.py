
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from qgis.core import QgsApplication, QgsVectorLayer, QgsWkbTypes

from ..model.db_item import DBItemModel
from ..model.project import Project
from ..model.scratch_vector import ScratchVector
from ..model.mask import Mask, insert_mask, REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID, MASK_MACHINE_CODE
from ..model.cross_sections import CrossSections

from ..gp.sample_frame import SampleFrameTask
from .utilities import validate_name, add_standard_form_buttons

MESSAGE_CATEGORY = "SampleFrame"


class FrmSampleFrame(QtWidgets.QDialog):

    export_complete = pyqtSignal(Mask or None, str, bool, bool)

    def __init__(self, parent, project: Project, polygon_init: ScratchVector = None, cross_sections_init: CrossSections = None):

        self.qris_project = project
        self.sample_frame = None

        super(FrmSampleFrame, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New Sample Frame')

        # Set Cross Sections, set init if exists
        cross_sections = {id: xsection for id, xsection in self.qris_project.cross_sections.items()}
        self.cross_sections_model = DBItemModel(cross_sections)
        self.cboCrossSections.setModel(self.cross_sections_model)
        if cross_sections_init is not None:
            self.cboCrossSections.setCurrentIndex(self.cross_sections_model.getItemIndex(cross_sections_init))

        # Masks (filtered to just AOI)
        masks = {f'mask_{id}': mask for id, mask in self.qris_project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
        context = {f'context_{id}': layer for id, layer in self.qris_project.scratch_vectors.items() if QgsVectorLayer(f'{layer.gpkg_path}|layername={layer.fc_name}').geometryType() == QgsWkbTypes.PolygonGeometry}
        self.polygons = {**masks, **context}
        self.polygons_model = DBItemModel(self.polygons)
        self.cboFramePolygon.setModel(self.polygons_model)
        if polygon_init is not None:
            index = self.polygons_model.getItemIndex(polygon_init)
            if index is not None:
                self.cboFramePolygon.setCurrentIndex(index)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.sample_frame is not None:
            try:
                self.sample_frame.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A sample frame with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Sample Frame', str(ex))
                return
        else:
            try:
                self.sample_frame = insert_mask(self.qris_project.project_file, self.txtName.text(), self.qris_project.lookup_tables['lkp_mask_types'][REGULAR_MASK_TYPE_ID], self.txtDescription.toPlainText())
                self.qris_project.masks[self.sample_frame.id] = self.sample_frame
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A sample frame with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Sample Frame', str(ex))
                return

            try:
                db_item_polygon = self.cboFramePolygon.currentData(QtCore.Qt.UserRole)
                if isinstance(db_item_polygon, Mask):
                    polygon_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=aoi_features')
                    polygon_layer.setSubsetString(f'mask_id = {db_item_polygon.id}')
                else:
                    polygon_layer = QgsVectorLayer(f'{db_item_polygon.gpkg_path}|layername={db_item_polygon.fc_name}')
                cross_sections = self.cboCrossSections.currentData(QtCore.Qt.UserRole)
                cross_sections_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=cross_section_features')
                cross_sections_layer.setSubsetString(f'cross_section_id = {cross_sections.id}')
                out_path = f'{self.qris_project.project_file}|layername=mask_features'
                task = SampleFrameTask(polygon_layer, cross_sections_layer, out_path, self.sample_frame.id)

                # TODO task complete signal not firing in production mode...
                # -- PRODUCTION --
                # task.sample_frame_complete.connect(self.frame_complete)
                # QgsApplication.taskManager().addTask(task)

                # -- DEBUG --
                task.run()
                self.frame_complete(True)

            except Exception as ex:
                try:
                    self.sample_frame.delete(self.qris_project.project_file)
                except Exception as ex:
                    print('Error attempting to delete sample frame after the importing of features failed.')
                QtWidgets.QMessageBox.warning(self, 'Error Importing Sample Frame Features', str(ex))
                return

        super(FrmSampleFrame, self).accept()

    @pyqtSlot(bool)
    def frame_complete(self, result: bool):

        if result is True:
            self.export_complete.emit(self.sample_frame, MASK_MACHINE_CODE, True, True)

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblCrossSections = QtWidgets.QLabel()
        self.lblCrossSections.setText('Cross Sections')
        self.grid.addWidget(self.lblCrossSections, 1, 0, 1, 1)

        self.cboCrossSections = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboCrossSections, 1, 1, 1, 1)

        self.lblFramePolygon = QtWidgets.QLabel('Frame Polygon')
        self.grid.addWidget(self.lblFramePolygon, 2, 0, 1, 1)

        self.cboFramePolygon = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboFramePolygon, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'sampling_frames'))
