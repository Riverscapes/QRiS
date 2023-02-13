
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsVectorLayer

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.scratch_vector import ScratchVector
from ..model.mask import Mask, insert_mask, REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID, MASK_MACHINE_CODE
from ..model.cross_sections import CrossSections

from ..gp.feature_class_functions import import_mask
from ..gp.sample_frame import SampleFrameTask
from .utilities import validate_name, add_standard_form_buttons

MESSAGE_CATEGORY = "SampleFrame"


class FrmSampleFrame(QtWidgets.QDialog):

    export_complete = pyqtSignal(Mask or None, str, bool, bool)

    def __init__(self, parent, project: Project, polygon_init: ScratchVector = None, cross_sections_init: CrossSections = None):

        self.qris_project = project
        self.polygon_init = polygon_init
        self.cross_sections_init = cross_sections_init
        self.sample_frame = None

        super(FrmSampleFrame, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New Sample Frame')

        # TODO set initial cross section or polygon if provided

        # Set Cross Sections, set init if exists
        self.cross_sections = {id: xsection for id, xsection in self.qris_project.cross_sections.items()}
        self.cross_sections_model = DBItemModel(self.cross_sections)
        self.cboCrossSections.setModel(self.cross_sections_model)
        # self.cboAttribute.setModelColumn(1)

        # Masks (filtered to just AOI)
        self.polygons = {id: mask for id, mask in self.qris_project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
        self.polygons_model = DBItemModel(self.polygons)
        self.cboFramePolygon.setModel(self.polygons_model)
        # Default to no mask clipping
        # self.cboFramePolygon.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

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
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return
        else:
            try:
                self.sample_frame = insert_mask(self.qris_project.project_file, self.txtName.text(), self.qris_project.lookup_tables['lkp_mask_types'][REGULAR_MASK_TYPE_ID], self.txtDescription.toPlainText())
                self.qris_project.masks[self.sample_frame.id] = self.sample_frame
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return

            try:
                polygon = self.cboFramePolygon.currentData(QtCore.Qt.UserRole)
                polygon_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=aoi_features')
                polygon_layer.setSubsetString(f'mask_id = {polygon.id}')
                cross_sections = self.cboCrossSections.currentData(QtCore.Qt.UserRole)
                cross_sections_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=cross_section_features')
                cross_sections_layer.setSubsetString(f'cross_section_id = {cross_sections.id}')
                out_path = f'{self.qris_project.project_file}|layername=mask_features'
                task = SampleFrameTask(polygon_layer, cross_sections_layer, out_path, self.sample_frame.id)
                task.sample_frame_complete.connect(self.on_complete)
                QgsApplication.taskManager().addTask(task)
                # task.run()
            except Exception as ex:
                try:
                    self.sample_frame.delete(self.qris_project.project_file)
                except Exception as ex:
                    print('Error attempting to delete mask after the importing of features failed.')
                QtWidgets.QMessageBox.warning(self, 'Error Importing Mask Features', str(ex))
                return

        super(FrmSampleFrame, self).accept()

    def on_complete(self):

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

        self.vert.addLayout(add_standard_form_buttons(self, 'masks'))
