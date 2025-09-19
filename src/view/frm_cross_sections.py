import json

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature
from qgis.utils import Qgis, iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.cross_sections import CrossSections, insert_cross_sections

from ..gp.feature_class_functions import import_existing, layer_path_parser
from ..gp.import_temp_layer import ImportMapLayer

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, add_standard_form_buttons

from typing import Dict


class FrmCrossSections(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str = None, cross_sections: CrossSections = None, output_features: Dict[float, QgsFeature] = None, metadata: dict = None):

        self.qris_project = project
        self.cross_sections = cross_sections
        self.import_source_path = import_source_path
        self.output_features = output_features

        super(FrmCrossSections, self).__init__(parent)
        metadata_json = json.dumps(cross_sections.metadata) if cross_sections is not None else None
        if metadata is not None:
            metadata_json = json.dumps(metadata)
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        window_title = 'Create New Cross Sections layer' if self.cross_sections is None else 'Edit Cross Sections Properties'

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = import_source_path is not None
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        show_mask_clip = import_source_path is not None or output_features is not None
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            window_title = 'Import Cross Sections'
            if isinstance(import_source_path, QgsVectorLayer):
                window_title = 'Import Cross Sections from Temporary Layer'
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                # show_attribute_filter = False
                # show_mask_clip = False
            else:
                # find if import_source_path is shapefile, geopackage, or other
                self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = import_source_path if isinstance(import_source_path, QgsVectorLayer) else QgsVectorLayer(import_source_path)
                self.no_attribute = DBItem('None', 0, 'None - No cross section ids')
                self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
                self.attributes[-1] = self.no_attribute
                self.attribute_model = DBItemModel(self.attributes)
                self.cboAttribute.setModel(self.attribute_model)
                self.cboAttribute.setCurrentIndex(self.attribute_model.getItemIndex(self.no_attribute))
        if show_mask_clip:
            # combine the valley bottom and aoi dicts; wwe need to adjust the keys for the aois to avoid conflicts
            self.masks = {}
            for key, value in  self.qris_project.valley_bottoms.items():
                self.masks[key] = value
            for key, value in self.qris_project.aois.items():
                self.masks[key + 1000] = value
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

        self.setWindowTitle(window_title)
        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        if self.cross_sections is not None:
            try:
                self.cross_sections.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
                super(FrmCrossSections, self).accept()
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A cross sections layer with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving cross sections', str(ex))
                self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                return

        else:
            try:
                self.cross_sections = insert_cross_sections(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
                self.qris_project.cross_sections[self.cross_sections.id] = self.cross_sections
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A cross sections layer with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving cross sections', str(ex))
                self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                return
            try:
                clip_mask = None
                clip_item:DBItem = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                if clip_item is not None:
                    if clip_item.id > 0:      
                        clip_mask = (clip_item.fc_name, clip_item.fc_id_column_name, clip_item.id)
                
                if self.import_source_path is not None:
                    attributes = {'cross_section_id': self.cross_sections.id}
                    # if the selected value of cboAttribute is not the no_attribute, then set the attribute to the display_label
                    if self.cboAttribute.isVisible() and self.cboAttribute.currentData(QtCore.Qt.UserRole) != self.no_attribute:
                        attributes['display_label'] = self.cboAttribute.currentData(QtCore.Qt.UserRole).name
                    if self.layer_id == 'memory':
                        fc_name = f'{self.qris_project.project_file}|layername=cross_section_features'
                        task = ImportMapLayer(self.import_source_path, fc_name, attributes, clip_mask=clip_mask, proj_gpkg=self.qris_project.project_file)
                        result = task.run()
                        self.on_import_complete(result)
                        # this is getting stuck if run as a task:
                        # task.import_complete.connect(self.on_import_complete)
                        # QgsApplication.taskManager().addTask(task)
                    else:
                        import_existing(self.import_source_path, self.qris_project.project_file, 'cross_section_features', self.cross_sections.id, 'cross_section_id', attributes, clip_mask)
                        super(FrmCrossSections, self).accept()
                elif self.output_features is not None:
                    out_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=cross_section_features')
                    clip_geom = None
                    if clip_mask is not None:
                        clip_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername={clip_mask[0]}')
                        clip_layer.setSubsetString(f'{clip_mask[1]} = {clip_mask[2]}')
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

            except Exception as ex:
                try:
                    self.cross_sections.delete(self.qris_project.project_file)
                except Exception as ex_del:
                    QtWidgets.QMessageBox.warning(self, 'Error attempting to delete cross sections after the importing of features failed.', str(ex_del))
                QtWidgets.QMessageBox.warning(self, 'Error Importing Cross Sections Features', str(ex))
                self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                return

            super(FrmCrossSections, self).accept()

    def on_import_complete(self, result: bool):

        if not result:
            iface.messageBar().pushMessage('Error Importing Cross Section Features', str(self.exception), level=Qgis.Critical)
            try:
                self.cross_sections.delete(self.qris_project.project_file)
            except Exception as ex:
                iface.messageBar().pushMessage('Error Deleting Cross Sections on Failed Import', str(ex), level=Qgis.Critical)
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
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QtWidgets.QGridLayout()

        self.lblName = QtWidgets.QLabel("Name")
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('Name of the cross sections layer')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblAttribute = QtWidgets.QLabel('Display Label Attribute')
        self.grid.addWidget(self.lblAttribute, 1, 0, 1, 1)

        self.cboAttribute = QtWidgets.QComboBox()
        self.cboAttribute.setToolTip('Attribute to use as the display label for the cross sections')
        self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI/Valley Bottom')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.cboMaskClip.setToolTip('Optionally clip the cross sections to the selected AOI or Valley Bottom')
        self.grid.addWidget(self.cboMaskClip, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Basic Properties')
        self.tabProperties.setLayout(self.grid)

        # Metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.chkAddToMap = QtWidgets.QCheckBox('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'cross-sections'))
