import json

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature
from qgis.utils import Qgis, iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.cross_sections import CrossSections, insert_cross_sections
from ..model.mask import AOI_MASK_TYPE_ID

from ..gp.feature_class_functions import import_existing, layer_path_parser
from ..gp.import_temp_layer import ImportTemporaryLayer
from .utilities import validate_name, add_standard_form_buttons

from typing import Dict


class FrmCrossSections(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str = None, cross_sections: CrossSections = None, output_features: Dict[float, QgsFeature] = None):

        self.project = project
        self.cross_sections = cross_sections
        self.import_source_path = import_source_path
        self.output_features = output_features
        self.metadata = None

        super(FrmCrossSections, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New Cross Sections layer')

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = import_source_path is not None
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        show_mask_clip = import_source_path is not None or output_features is not None
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                show_attribute_filter = False
                show_mask_clip = False
            else:
                # find if import_source_path is shapefile, geopackage, or other
                self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = import_source_path if isinstance(import_source_path, QgsVectorLayer) else QgsVectorLayer(import_source_path)
                self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
                self.attribute_model = DBItemModel(self.attributes)
                self.cboAttribute.setModel(self.attribute_model)
                # self.cboAttribute.setModelColumn(1)
        if show_mask_clip:
            # Masks (filtered to just AOI)
            self.masks = {id: mask for id, mask in self.project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
            no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
            self.masks[0] = no_clipping
            self.masks_model = DBItemModel(self.masks)
            self.cboMaskClip.setModel(self.masks_model)
            # Default to no mask clipping
            self.cboMaskClip.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

        if self.cross_sections is not None:
            self.txtName.setText(cross_sections.name)
            self.txtDescription.setPlainText(cross_sections.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def add_metadata(self, metadata):
        self.metadata = metadata

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.cross_sections is not None:
            try:
                self.cross_sections.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A cross sections layer with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving cross sections', str(ex))
                return
        else:
            try:
                self.cross_sections = insert_cross_sections(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), json.dumps(self.metadata))
                self.project.cross_sections[self.cross_sections.id] = self.cross_sections
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A cross sections layer with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving cross sections', str(ex))
                return
            try:
                clip_mask = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                clip_mask_id = None
                if clip_mask is not None:
                    clip_mask_id = clip_mask.id if clip_mask.id > 0 else None
                if self.import_source_path is not None:
                    if self.layer_id == 'memory':
                        task = ImportTemporaryLayer(self.import_source_path, self.project.project_file, 'cross_section_features', 'cross_section_id', self.cross_sections.id, clip_mask_id, proj_gpkg=self.project.project_file)
                        task.import_complete.connect(self.on_import_complete)
                        QgsApplication.taskManager().addTask(task)
                    else:
                        attributes = {self.cboAttribute.currentData(QtCore.Qt.UserRole).name: 'display_label'} if self.cboAttribute.isVisible() else {}
                        import_existing(self.import_source_path, self.project.project_file, 'cross_section_features', self.cross_sections.id, 'cross_section_id', attributes, clip_mask_id)
                        super(FrmCrossSections, self).accept()
                elif self.output_features is not None:
                    out_layer = QgsVectorLayer(f'{self.project.project_file}|layername=cross_section_features')
                    clip_geom = None
                    if clip_mask_id is not None:
                        clip_layer = QgsVectorLayer(f'{self.project.project_file}|layername=aoi_features')
                        clip_layer.setSubsetString(f'mask_id = {clip_mask_id}')
                        clip_feats = clip_layer.getFeatures()
                        clip_feat = QgsFeature()
                        clip_feats.nextFeature(clip_feat)
                        clip_geom = clip_feat.geometry()
                    for sequence, out_feature in self.output_features.items():
                        out_feature.setFields(out_layer.fields())
                        out_feature['sequence'] = sequence
                        out_feature['cross_section_id'] = self.cross_sections.id
                        if clip_geom is not None:
                            geom = out_feature.geometry()
                            out_geom = geom.intersection(clip_geom)
                            out_feature.setGeometry(out_geom)
                        out_layer.dataProvider().addFeature(out_feature)
                    out_layer.commitChanges()
                    super(FrmCrossSections, self).accept()
            except Exception as ex:
                try:
                    self.cross_sections.delete(self.project.project_file)
                except Exception as ex_del:
                    QtWidgets.QMessageBox.warning(self, 'Error attempting to delete cross sections after the importing of features failed.', str(ex_del))
                QtWidgets.QMessageBox.warning(self, 'Error Importing Cross Sections Features', str(ex))

    def on_import_complete(self, result: bool):

        if not result:
            QtWidgets.QMessageBox.warning(self, f'Error Importing Cross Section Features', str(self.exception))
            try:
                self.cross_sections.delete(self.qris_project.project_file)
            except Exception as ex:
                print(f'Error attempting to delete Cross Section after the importing of features failed.')
            return
        else:
            iface.messageBar().pushMessage('Cross Section Import Complete.', f"{self.import_source_path} saved successfully.", level=Qgis.Info, duration=5)
            super(FrmCrossSections, self).accept()

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

        self.lblAttribute = QtWidgets.QLabel()
        self.lblAttribute.setText('Attribute')
        self.grid.addWidget(self.lblAttribute, 1, 0, 1, 1)

        self.cboAttribute = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel()
        self.lblMaskClip.setText('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMaskClip, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'cross_sections'))
