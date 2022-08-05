# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRiSDockWidget
                                 A QGIS plugin
 QGIS Riverscapes Studio (QRiS)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-05-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.core import QgsMapLayer
from qgis.gui import QgsDataSourceSelectDialog
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog, QMenu, QMessageBox, QDockWidget
from qgis.PyQt.QtCore import pyqtSignal, Qt, QDate, pyqtSlot, QUrl
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon, QDesktopServices

from ..model.layer import Layer
from ..model.project import Project
from ..model.event import Event
from ..model.event import EVENT_MACHINE_CODE
from ..model.basemap import BASEMAP_MACHINE_CODE, PROTOCOL_BASEMAP_MACHINE_CODE, Basemap
from ..model.mask import MASK_MACHINE_CODE
from ..model.analysis import ANALYSIS_MACHINE_CODE, Analysis
from ..model.db_item import DB_MODE_CREATE, DB_MODE_IMPORT, DBItem
from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.basemap import BASEMAP_MACHINE_CODE, Basemap
from ..model.mask import MASK_MACHINE_CODE, Mask
from ..model.protocol import Protocol

from .frm_design2 import FrmDesign
from .frm_event import DATA_CAPTURE_EVENT_TYPE_ID
from .frm_event import FrmEvent
from .frm_basemap import FrmBasemap
from .frm_mask_aoi import FrmMaskAOI
from .frm_new_analysis import FrmNewAnalysis
from .frm_new_project import FrmNewProject

from ..QRiS.settings import Settings
from ..QRiS.method_to_map import build_basemap_layer, get_project_group, remove_db_item_layer, check_for_existing_layer
from ..QRiS.method_to_map import build_event_protocol_single_layer, build_basemap_layer, build_mask_layer

from .ui.qris_dockwidget import Ui_QRiSDockWidget

from ..gp.feature_class_functions import browse_source

SCRATCH_NODE_TAG = 'SCRATCH'


class QRiSDockWidget(QDockWidget, Ui_QRiSDockWidget):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(QRiSDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.settings = Settings()

        self.qris_project = None
        self.menu = QMenu()

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)
        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

    # Take this out of init so that nodes can be added as new data is added and imported;
    def build_tree_view(self, project_file, new_item=None):
        """Builds items in the tree view based on dictionary values that are part of the project"""
        self.project = Project(project_file)

        self.model.clear()
        self.tree_state = {}
        rootNode = self.model.invisibleRootItem()

        # set the project root
        project_node = QStandardItem(self.project.name)
        project_node.setIcon(QIcon(':/plugins/qris_toolbar/icon.png'))
        project_node.setData(self.project, Qt.UserRole)
        rootNode.appendRow(project_node)
        # self.treeView.setExpanded(project_node.index(), True)

        events_node = QStandardItem('Data Capture Events')
        events_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        events_node.setData(EVENT_MACHINE_CODE, Qt.UserRole)
        project_node.appendRow(events_node)
        [self.add_event_too_tree(events_node, item) for item in self.project.events.values()]

        basemaps_node = QStandardItem('Basemaps')
        basemaps_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        basemaps_node.setData(BASEMAP_MACHINE_CODE, Qt.UserRole)
        project_node.appendRow(basemaps_node)
        [self.add_child_node(item, basemaps_node, 'test_layers.png') for item in self.project.basemaps.values()]

        masks_node = QStandardItem('Masks')
        masks_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        masks_node.setData(MASK_MACHINE_CODE, Qt.UserRole)
        project_node.appendRow(masks_node)
        [self.add_child_node(item, masks_node, 'test_layers.png') for item in self.project.masks.values()]

        # scratch_node = QStandardItem('Scratch Space')
        # scratch_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        # scratch_node.setData(SCRATCH_NODE_TAG, Qt.UserRole)
        # project_node.appendRow(scratch_node)

        # analyses_node = QStandardItem('Analyses')
        # analyses_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        # analyses_node.setData(ANALYSIS_MACHINE_CODE, Qt.UserRole)
        # analyses_node.appendRow(analyses_node)

        self.treeView.expandAll()
        return

        # Check if new item is in the tree, if it is pass it to the add_to_map function
        # Adds a test comment
        if new_item is not None and new_item != '':
            selected_item = self._find_item_in_model(new_item)
            if selected_item is not None:
                add_to_map(self.qris_project, self.model, selected_item)

    def add_child_node(self, db_item: DBItem, parent_node: QStandardItem, icon_file_name: str):

        node = QStandardItem(db_item.name)
        node.setIcon(QIcon(':plugins/qris_toolbar/{}'.format(icon_file_name)))
        node.setData(db_item, Qt.UserRole)
        parent_node.appendRow(node)

    def _find_item_in_model(self, name):
        """Looks in the tree for an item name passed from the dataChange method."""
        # TODO may want to pass this is a try except block and give an informative error message
        selected_item = self.model.findItems(name, Qt.MatchRecursive)[0]
        return selected_item

    def get_item_expanded_state(self):
        """Recursively records a list of the expanded state for items in the tree"""

    def closeEvent(self, event):
        self.qris_project = None
        self.closingPlugin.emit()
        event.accept()

    def open_menu(self, position):
        """Connects signals as context menus to items in the tree"""
        self.menu.clear()
        indexes = self.treeView.selectedIndexes()
        if len(indexes) < 1:
            return

        # No multiselect so there is only ever one item
        idx = indexes[0]
        if not idx.isValid():
            return

        model_item = self.model.itemFromIndex(indexes[0])
        model_data = model_item.data(Qt.UserRole)

        if isinstance(model_data, str):
            if model_data == ANALYSIS_MACHINE_CODE:
                self.add_context_menu_item(self.menu, 'Create New Analysis', 'test_new.png', lambda: self.add_analysis(model_item, DB_MODE_CREATE))
            else:
                self.add_context_menu_item(self.menu, 'Add To Map', 'test_add_map.png', lambda: self.add_tree_group_to_map(model_item))
                if model_data == EVENT_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Add New Data Capture Event', 'test_new.png', lambda: self.add_event(model_item, DATA_CAPTURE_EVENT_TYPE_ID))
                    self.add_context_menu_item(self.menu, 'Add New Design', 'test_new.png', lambda: self.add_event(model_item, 0))
                elif model_data == BASEMAP_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Import Existing Basemap Dataset', 'test_new.png', lambda: self.add_basemap(model_item))
                elif model_data == MASK_MACHINE_CODE:
                    add_mask_menu = self.menu.addMenu('Create New')
                    self.add_context_menu_item(add_mask_menu, 'Area of Interest', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_CREATE))
                    self.add_context_menu_item(add_mask_menu, 'Regular Masks', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_CREATE), False)
                    self.add_context_menu_item(add_mask_menu, 'Directional Masks', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_CREATE), False)

                    import_mask_menu = self.menu.addMenu('Import Existing')
                    self.add_context_menu_item(import_mask_menu, 'Area of Interest', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_IMPORT))
                    self.add_context_menu_item(import_mask_menu, 'Regular Masks', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_IMPORT), False)
                    self.add_context_menu_item(import_mask_menu, 'Directional Masks', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_IMPORT), False)

                    # self.add_context_menu_item(self.menu, 'Create New Empty Mask', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_CREATE))
                    # self.add_context_menu_item(self.menu, 'Import Existing Mask Feature Class', 'test_new.png', lambda: self.add_mask(model_item, DB_MODE_IMPORT))
                else:
                    f'Unhandled group folder clicked in QRiS project tree: {model_data}'
        else:
            if isinstance(model_data, DBItem):
                self.add_context_menu_item(self.menu, 'Add To Map', 'test_add_map.png', lambda: self.add_db_item_to_tree(model_item, model_data))
            else:
                raise Exception('Unhandled group folder clicked in QRiS project tree: {}'.format(model_data))

            if isinstance(model_data, Project) or isinstance(model_data, Event) or isinstance(model_data, Basemap) or isinstance(model_data, Mask):
                self.add_context_menu_item(self.menu, 'Edit', 'Options.png', lambda: self.edit_item(model_item, model_data))

            if isinstance(model_data, Project):
                self.add_context_menu_item(self.menu, 'Browse Containing Folder', 'RaveAddIn.png', lambda: self.browse_item(model_data))
            else:
                self.add_context_menu_item(self.menu, 'Delete', 'RaveAddIn.png', lambda: self.delete_item(model_item, model_data))

        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_context_menu_item(self, menu: QMenu, menu_item_text: str, icon_file_nam, slot: pyqtSlot = None, enabled=True):
        action = menu.addAction(QIcon(':/plugins/qris_toolbar/{}'.format(icon_file_nam)), menu_item_text)
        action.setEnabled(enabled)

        if slot is not None:
            action.triggered.connect(slot)

    def add_db_item_to_tree(self, tree_node: QStandardItem, db_item: DBItem):

        if isinstance(db_item, Mask):
            build_mask_layer(self.project, db_item)
        elif isinstance(db_item, Basemap):
            build_basemap_layer(self.project, db_item)
        elif isinstance(db_item, Event):
            [build_event_protocol_single_layer(self.project, event_layer) for event_layer in db_item.event_layers]
        elif isinstance(db_item, Protocol):
            # determine parent node
            event_node = tree_node.parent()
            event = event_node.data(Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer in db_item.layers:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Layer):
            # determine parent node
            event_node = tree_node.parent().parent()
            event = event_node.data(Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer == db_item:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Project):
            [build_mask_layer(mask) for mask in self.project.masks.values()]
            [build_basemap_layer(basemap) for basemap in self.project.basemaps.values()]
            [[build_event_protocol_single_layer(self.project, event_layer) for event_layer in event.event_layers] for event in self.project.events.values()]

    def add_tree_group_to_map(self, model_item: QStandardItem):
        """Add all children of a group node to the map ToC
        """

        for row in range(0, model_item.rowCount()):
            child_item = model_item.child(row)
            self.add_db_item_to_tree(child_item, child_item.data(Qt.UserRole))

    def expand_tree(self):
        self.treeView.expandAll()
        return

    def collapse_tree(self):
        self.treeView.collapseAll()
        return

    def add_event(self, parent_node, event_type_id: int):
        """Initiates adding a new data capture event"""
        if event_type_id == DATA_CAPTURE_EVENT_TYPE_ID:
            frm = FrmEvent(self, self.project)
        else:
            frm = FrmDesign(self, self.project)

        # self.assessment_dialog.dateEdit_assessment_date.setDate(QDate.currentDate())
        # self.assessment_dialog.dataChange.connect(self.build_tree_view)
        result = frm.exec_()
        if result is not None and result != 0:
            self.add_event_too_tree(parent_node, frm.event)

            # if frm.chkAddToMap.isChecked():
            #     for method_id in event.protocols:
            #         add_to_map(self.project, method_id)

    def add_event_too_tree(self, parent_node, event: Event):

        event_node = QStandardItem(event.name)
        event_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
        event_node.setData(event, Qt.UserRole)
        parent_node.appendRow(event_node)

        for protocol in event.protocols:
            protocol_node = QStandardItem(protocol.name)
            protocol_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
            protocol_node.setData(protocol, Qt.UserRole)
            event_node.appendRow(protocol_node)

            for layer in protocol.layers:
                if layer.is_lookup is False:
                    layer_node = QStandardItem(layer.name)
                    layer_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
                    layer_node.setData(layer, Qt.UserRole)
                    protocol_node.appendRow(layer_node)

        # Basemaps
        basemap_group_node = QStandardItem('Basemaps')
        basemap_group_node.setIcon(QIcon(':plugins/qris_toolbar/BrowseFolder.png'))
        basemap_group_node.setData(PROTOCOL_BASEMAP_MACHINE_CODE, Qt.UserRole)
        event_node.appendRow(basemap_group_node)
        for basemap in event.basemaps:
            basemap_node = QStandardItem(basemap.name)
            basemap_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
            basemap_node.setData(basemap, Qt.UserRole)
            basemap_group_node.appendRow(basemap_node)

    def add_assessment_method(self, project: Project, protocol: Protocol):

        # if method.id == 3:
        frm = FrmDesign(self, self.project)
        result = frm.exec_()

        # QMessageBox.warning(self, 'Add', 'Adding Assessment Method Directly Is Not Yet Implemented.')

    def add_basemap(self, parent_node):
        """Initiates adding a new basis"""

        import_source_path = browse_source(self, 'Select a raster dataset to import as a new basis dataset.', QgsMapLayer.RasterLayer)
        if import_source_path is None:
            return

        frm = FrmBasemap(self, self.project, import_source_path)
        result = frm.exec_()
        if result != 0:
            new_node = QStandardItem(frm.basemap.name)
            new_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
            new_node.setData(frm.basemap, Qt.UserRole)
            parent_node.appendRow(new_node)

            if frm.chkAddToMap.isChecked():
                build_basemap_layer(self.project, frm.basemap)

    def add_mask(self, parent_node, mode):
        """Initiates adding a new mask"""

        get_project_group(self.project)

        import_source_path = None
        if mode == DB_MODE_IMPORT:
            import_source_path = browse_source(self, 'Select a polygon dataset to import as a new mask.', QgsMapLayer.VectorLayer)
            if import_source_path is None:
                return

        frm = FrmMaskAOI(self, self.project, import_source_path)
        result = frm.exec_()
        if result != 0:
            mask = frm.mask
            new_node = QStandardItem(mask.name)
            new_node.setIcon(QIcon(':plugins/qris_toolbar/icon.png'))
            new_node.setData(mask, Qt.UserRole)
            parent_node.appendRow(new_node)

            if frm.chkAddToMap.isChecked():
                build_mask_layer(self.project, mask)

    # def add_assessment_to_map(self, assessment):
    #     for method_id in assessment.methods.keys():
    #         add_assessment_method_to_map(self.project, method_id)

    # def add_to_map(self, db_item: DBItem):
    #     add_mask_to_map(self.project, db_item)

    def add_analysis(self, parent_node, mode):

        frm = FrmNewAnalysis(self, self.project)
        # result = frm.exec_()
        # if result!=0:
        #     analysis =

    # def add_assessment_to_map(self, event: Event):
    #     for protocol_id in event.protocols.keys():
    #         add_assessment_method_to_map(self.project, protocol_id)

    # def add_to_map(self, db_item: DBItem):
    #     add_root_map_item(self.project, db_item)

    def edit_item(self, model_item: QStandardItem, db_item: DBItem):

        frm = None
        if isinstance(db_item, Project):
            frm = FrmNewProject(os.path.dirname(db_item.project_file), parent=self, project=db_item)
        elif isinstance(db_item, Event):
            frm = FrmEvent(self, self.project, db_item)
        elif isinstance(db_item, Mask):
            frm = FrmMaskAOI(parent=self, project=self.project, import_source_path=None, mask=db_item)
        elif isinstance(db_item, Basemap):
            frm = FrmBasemap(self, self.project, None, db_item)
        else:
            QMessageBox.warning(self, 'Delete', 'Editing items is not yet implemented.')

        if frm is not None:
            result = frm.exec_()
            if result is not None and result != 0:
                model_item.setText(frm.txtProjectName.text())
                # This will check if the item is in the map and update its name if it is
                check_for_existing_layer(self.project, db_item)

    def delete_item(self, model_item: QStandardItem, db_item: DBItem):

        response = QMessageBox.question(self, 'Confirm Delete', 'Are you sure that you want to delete the selected item?')
        if response == QMessageBox.No:
            return

        # Remove the layer from the map first
        remove_db_item_layer(self.project, db_item)

        # Remove the item from the project tree
        model_item.parent().removeRow(model_item.row())

        # Remove the item from the project
        self.project.remove(db_item)

        # Delete the item from the database
        db_item.delete(self.project.project_file)

    def browse_item(self, db_item: DBItem):

        folder_path = None
        if isinstance(db_item, Basemap):
            folder_path = os.path.join(os.path.dirname(self.project.project_file), db_item.path)
        else:
            folder_path = self.project.project_file

        while not os.path.isdir(folder_path):
            folder_path = os.path.dirname(folder_path)

        qurl = QUrl.fromLocalFile(folder_path)
        QDesktopServices.openUrl(qurl)

    def add_structure_type(self):
        """Initiates adding a structure type and the structure type dialog"""
        # TODO First check if the path to the database exists
        design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        if os.path.exists(design_geopackage_path):
            self.structure_type_dialog = StructureTypeDlg(self.qris_project)
            self.structure_type_dialog.dataChange.connect(self.build_tree_view)
            self.structure_type_dialog.show()
        else:
            # TODO move the creation of the design data model so that this isn't necessary
            QMessageBox.information(self, "Structure Types", "Please create a new project design before adding structure types")

    def add_zoi_type(self):
        """Initiates adding a zoi type and the zoi type dialog"""
        # TODO First check if the path to the database exists
        design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        if os.path.exists(design_geopackage_path):
            self.zoi_type_dialog = ZoiTypeDlg(self.qris_project)
            self.zoi_type_dialog.dataChange.connect(self.build_tree_view)
            self.zoi_type_dialog.show()
        else:
            # TODO move the creation of the design data model so that this isn't necessary
            QMessageBox.information(self, "Structure Types", "Please create a new project design before adding a new influence type")

    def add_phase(self):
        """Initiates adding a new phase within the phase dialog"""
        # TODO First check if the path to the database exists
        design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        if os.path.exists(design_geopackage_path):
            self.phase_dialog = PhaseDlg(self.qris_project)
            self.phase_dialog.dataChange.connect(self.build_tree_view)
            self.phase_dialog.show()
        else:
            # TODO move the creation of the design data model so that this isn't necessary
            QMessageBox.information(self, "Structure Types", "Please create a new project design before adding phases")

    # This will kick off importing photos
    def import_photos(self):
        pass

    def add_detrended_raster(self):
        # last_browse_path = self.settings.getValue('lastBrowsePath')
        # last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None
        dialog_return = QFileDialog.getOpenFileName(None, "Add Detrended Raster to QRiS project", None, self.tr("Raster Data Sources (*.tif)"))
        if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
            self.addDetrendedDlg = AddDetrendedRasterDlg(None, dialog_return[0], self.qris_project)
            self.addDetrendedDlg.dataChange.connect(self.build_tree_view)
            self.addDetrendedDlg.exec()

    def import_project_extent_layer(self):
        """launches the dialog that supports import of a project extent layer polygon"""
        select_layer = QgsDataSourceSelectDialog()
        select_layer.exec()
        uri = select_layer.uri()
        if uri is not None and uri.isValid() and uri.wkbType == 3:
            self.project_extent_dialog = ProjectExtentDlg(uri, self.qris_project)
            self.project_extent_dialog.dataChange.connect(self.build_tree_view)
            self.project_extent_dialog.exec_()
        else:
            QMessageBox.critical(self, "Invalid Layer", "Please select a valid polygon layer")

    def create_blank_project_extent(self):
        """Adds a blank project extent that will be edited by the user"""
        self.project_extent_dialog = ProjectExtentDlg(None, self.qris_project)
        self.project_extent_dialog.dataChange.connect(self.build_tree_view)
        self.project_extent_dialog.exec_()

    def update_project_extent(self):
        """Renames the project extent layer"""
        pass

    # def delete_project_extent(self, selected_item):
    #     """Deletes a project extent layer"""
    #     display_name = selected_item.data(item_code['INSTANCE']).display_name
    #     feature_name = selected_item.data(item_code['INSTANCE']).feature_name
    #     geopackage_path = selected_item.data(item_code['INSTANCE']).geopackage_path(self.qris_project.project_path)

    #     delete_ok = QMessageBox.question(self, f"Delete extent", f"Are you fucking sure you wanna delete the extent layer: {display_name}")
    #     if delete_ok == QMessageBox.Yes:
    #         # remove from the map if it's there
    #         # TODO consider doing this based on the path
    #         for layer in QgsProject.instance().mapLayers().values():
    #             if layer.name() == display_name:
    #                 QgsProject.instance().removeMapLayers([layer.id()])
    #                 iface.mapCanvas().refresh()

    #         # TODO be sure to test whether the table exists first
    #         gdal_delete = gdal.OpenEx(geopackage_path, gdal.OF_UPDATE, allowed_drivers=['GPKG'])
    #         error = gdal_delete.DeleteLayer(feature_name)
    #         gdal_delete.ExecuteSQL('VACUUM')
    #         # TODO remove this from the Extents dictionary that will also remove from promect xml
    #         del(self.qris_project.project_extents[feature_name])
    #         # refresh the project xml
    #         self.qris_project.write_project_xml()
    #         # refresh the tree
    #         self.build_tree_view(self.qris_project, None)
    #     else:
    #         QMessageBox.information(self, "Delete extent", "No layers were deleted")

    def import_project_layer(self):
        """launches a dialog that supports import of project layers that can be clipped to a project extent"""
        select_layer = QgsDataSourceSelectDialog()
        select_layer.exec()
        uri = select_layer.uri()
        if uri is not None and uri.isValid():  # and uri.wkbType == 3:
            self.project_layer_dialog = ProjectLayerDlg(uri, self.qris_project)
            self.project_layer_dialog.dataChange.connect(self.build_tree_view)
            self.project_layer_dialog.exec_()
        else:
            QMessageBox.critical(self, "Invalid Layer", "Please select a valid gis layer")

    def explore_elevations(self, selected_item):
        # raster = selected_item.data(item_code['INSTANCE'])
        self.elevation_widget = ElevationDockWidget(raster, self.qris_project)
        self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
        self.elevation_widget.dataChange.connect(self.build_tree_view)
        self.elevation_widget.show()
