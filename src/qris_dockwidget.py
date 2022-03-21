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

from osgeo import gdal

from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsExpressionContextUtils,
    QgsVectorFileWriter)

from qgis.gui import QgsDataSourceSelectDialog
from qgis.utils import iface

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt, QDate
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon

from .QRiS.context_menu import ContextMenu
from .QRiS.settings import Settings
from .QRiS.qt_user_role import item_code
from .QRiS.manage_map import add_to_map

from .ui.elevation_dockwidget import ElevationDockWidget
from .ui.project_extent_dialog import ProjectExtentDlg
from .ui.project_layer_dialog import ProjectLayerDlg
from .ui.add_detrended_dialog import AddDetrendedRasterDlg
from .ui.assessment_dialog import AssessmentDlg
from .ui.design_dialog import DesignDlg
from .ui.structure_type_dialog import StructureTypeDlg
from .ui.zoi_type_dialog import ZoiTypeDlg
from .ui.phase_dialog import PhaseDlg

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qris_dockwidget.ui'))


class QRiSDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

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
        self.menu = ContextMenu()

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)
        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

    # Take this out of init so that nodes can be added as new data is added and imported;
    def build_tree_view(self, qris_project, new_item=None):
        """Builds items in the tree view based on dictionary values that are part of the project"""
        self.qris_project = qris_project

        self.model.clear()
        rootNode = self.model.invisibleRootItem()

        # set the project root
        project_node = QStandardItem(self.qris_project.project_name)
        project_node.setIcon(QIcon(':/plugins/qris_toolbar/test_Riverscapes.png'))
        project_node.setData('project_root', item_code['item_type'])
        rootNode.appendRow(project_node)

        # Add project extent layers to tree
        extent_folder = QStandardItem("Project Extents")
        extent_folder.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        extent_folder.setData('extent_folder', item_code['item_type'])
        project_node.appendRow(extent_folder)

        for extent in self.qris_project.project_extents.values():
            extent_node = QStandardItem(extent.display_name)
            extent_node.setIcon(QIcon(':/plugins/qris_toolbar/layers/Polygon.png'))
            extent_node.setData('extent_node', item_code['item_type'])
            extent_node.setData(extent, item_code['INSTANCE'])
            extent_folder.appendRow(extent_node)

        # Add project layers node
        layers_folder = QStandardItem("Project Layers")
        layers_folder.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        layers_folder.setData('layers_folder', item_code['item_type'])
        project_node.appendRow(layers_folder)

        # TODO extend this for geometry types and raster layers
        for layer in self.qris_project.project_vector_layers.values():
            layer_node = QStandardItem(layer.display_name)
            # TODO change icon by type
            layer_node.setIcon(QIcon(':/plugins/qris_toolbar/layers/Polyline.png'))
            layer_node.setData('layer_node', item_code['item_type'])
            layer_node.setData(layer, item_code['INSTANCE'])
            layers_folder.appendRow(layer_node)

        # # Add riverscape surfaces node
        # # TODO go through and add layers to the tree
        # riverscape_surfaces_node = QStandardItem("Riverscape Surfaces")
        # riverscape_surfaces_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        # riverscape_surfaces_node.setData('riverscape_surfaces_folder', item_code['item_type'])
        # riverscape_surfaces_node.setData('group', item_code['item_layer'])
        # project_node.appendRow(riverscape_surfaces_node)

        # # Add riverscape segments node
        # # TODO go through and add layers to the tree
        # riverscape_segments_node = QStandardItem("Riverscape Segments")
        # riverscape_segments_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        # riverscape_segments_node.setData('riverscape_segments_folder', item_code['item_type'])
        # riverscape_segments_node.setData('group', item_code['item_layer'])
        # project_node.appendRow(riverscape_segments_node)

        # # Add detrended rasters to tree
        # detrended_rasters = QStandardItem("Detrended Rasters")
        # detrended_rasters.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        # detrended_rasters.setData("DetrendedRastersFolder", item_code['item_type'])
        # detrended_rasters.setData('group', item_code['item_layer'])
        # project_node.appendRow(detrended_rasters)

        # for raster in self.qris_project.detrended_rasters.values():
        #     detrended_raster = QStandardItem(raster.name)
        #     detrended_raster.setIcon(QIcon(':/plugins/qris_toolbar/qris_raster.png'))
        #     detrended_raster.setData('DetrendedRaster', item_code['item_type'])
        #     detrended_raster.setData(raster, item_code['INSTANCE'])
        #     detrended_raster.setData('raster_layer', item_code['item_layer'])
        #     detrended_rasters.appendRow(detrended_raster)

        #     if len(raster.surfaces.values()) > 0:
        #         item_surfaces = QStandardItem("Surfaces")
        #         item_surfaces.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        #         item_surfaces.setData('group', item_code['item_layer'])
        #         detrended_raster.appendRow(item_surfaces)
        #         for surface in raster.surfaces.values():
        #             item_surface = QStandardItem(surface.name)
        #             item_surface.setIcon(QIcon(':/plugins/qris_toolbar/layers/Polygon.png'))
        #             item_surface.setData('DetrendedRasterSurface', item_code['item_type'])
        #             item_surface.setData('surface_layer', item_code['item_layer'])
        #             item_surface.setData(surface, item_code['INSTANCE'])
        #             item_surfaces.appendRow(item_surface)

        # # Add assessments to tree
        # assessments_parent_node = QStandardItem("Riverscape Assessments")
        # assessments_parent_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        # assessments_parent_node.setData('assessments_folder', item_code['item_type'])
        # assessments_parent_node.setData('group', item_code['item_layer'])
        # project_node.appendRow(assessments_parent_node)

        # if self.qris_project.project_assessments:
        #     self.qris_project.assessments_path = os.path.join(self.qris_project.project_path, "Assessments.gpkg")
        #     assessments_layer = QgsVectorLayer(self.qris_project.assessments_path + "|layername=assessments", "assessments", "ogr")
        #     for assessment_feature in assessments_layer.getFeatures():
        #         assessment_node = QStandardItem(assessment_feature.attribute('assessment_date').toString('yyyy-MM-dd'))
        #         assessment_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        #         assessment_node.setData('dam_assessment', item_code['item_type'])
        #         assessment_node.setData('group', item_code['item_layer'])
        #         assessment_node.setData(assessment_feature.attribute('fid'), item_code['feature_id'])
        #         assessments_parent_node.appendRow(assessment_node)

        # assessments_parent_node.sortChildren(Qt.AscendingOrder)

        # Add designs to tree
        design_folder = QStandardItem("Low-Tech Designs")
        design_folder.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        design_folder.setData('design_folder', item_code['item_type'])
        project_node.appendRow(design_folder)

        design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        designs_path = design_geopackage_path + '|layername=designs'
        if os.path.exists(design_geopackage_path):
            designs_layer = QgsVectorLayer(designs_path, "designs", "ogr")
            for design_feature in designs_layer.getFeatures():
                # If these data types stick this should be refactored into a create node function
                design_node = QStandardItem(design_feature.attribute('name'))
                design_node.setIcon(QIcon(':/plugins/qris_toolbar/icon.png'))
                design_node.setData('design', item_code['item_type'])
                design_node.setData(design_feature.attribute('fid'), item_code['feature_id'])
                design_folder.appendRow(design_node)

                # TODO add the structure, footprint, and zoi to the tree under each design

            # TODO This just doesn't work very well
            design_folder.sortChildren(Qt.AscendingOrder)

        # populate structure types
        structure_type_folder = QStandardItem("Structure Types")
        structure_type_folder.setIcon(QIcon(':/plugins/qris_toolbar/Options.png'))
        structure_type_folder.setData('structure_type_folder', item_code['item_type'])
        design_folder.appendRow(structure_type_folder)

        structure_type_path = design_geopackage_path + '|layername=structure_types'
        structure_type_layer = QgsVectorLayer(structure_type_path, "structure_types", "ogr")
        for structure_type in structure_type_layer.getFeatures():
            structure_type_node = QStandardItem(structure_type.attribute('name'))
            # TODO change the icon
            structure_type_node.setIcon(QIcon(':/plugins/qris_toolbar/icon.png'))
            structure_type_node.setData('structure_type', item_code['item_type'])
            structure_type_node.setData(structure_type.attribute('fid'), item_code['feature_id'])
            structure_type_folder.appendRow(structure_type_node)

        # populate design phases types
        phase_folder = QStandardItem("Implementation Phases")
        # TODO change icon
        phase_folder.setIcon(QIcon(':/plugins/qris_toolbar/Options.png'))
        phase_folder.setData('phase_folder', item_code['item_type'])
        design_folder.appendRow(phase_folder)

        phase_path = design_geopackage_path + '|layername=phases'
        phase_layer = QgsVectorLayer(phase_path, "phases", "ogr")
        for phase in phase_layer.getFeatures():
            phase_node = QStandardItem(phase.attribute('name'))
            # TODO change the icon
            phase_node.setIcon(QIcon(':/plugins/qris_toolbar/icon.png'))
            phase_node.setData('phase', item_code['item_type'])
            phase_node.setData(phase.attribute('fid'), item_code['feature_id'])
            phase_folder.appendRow(phase_node)

        # populate zoi types
        zoi_type_folder = QStandardItem("ZOI Types")
        zoi_type_folder.setIcon(QIcon(':/plugins/qris_toolbar/Options.png'))
        zoi_type_folder.setData('zoi_type_folder', item_code['item_type'])
        design_folder.appendRow(zoi_type_folder)

        zoi_type_path = design_geopackage_path + '|layername=zoi_types'
        zoi_type_layer = QgsVectorLayer(zoi_type_path, "zoi_types", "ogr")
        for zoi_type in zoi_type_layer.getFeatures():
            zoi_type_node = QStandardItem(zoi_type.attribute('name'))
            # TODO change the icon
            zoi_type_node.setIcon(QIcon(':/plugins/qris_toolbar/icon.png'))
            zoi_type_node.setData('zoi_type', item_code['item_type'])
            zoi_type_node.setData(zoi_type.attribute('fid'), item_code['feature_id'])
            zoi_type_folder.appendRow(zoi_type_node)

        # Add a placed for photos
        # photos_folder = QStandardItem("Project Photos")
        # photos_folder.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        # photos_folder.setData('photos_folder', item_code['item_type'])
        # project_node.appendRow(photos_folder)

        # TODO for now we are expanding the map however need to remember expanded state or add new nodes as we add data
        self.treeView.expandAll()

        # Check if new item is in the tree, if it is pass it to the add_to_map function
        # Adds a test comment
        if new_item is not None and new_item != '':
            selected_item = self._find_item_in_model(new_item)
            if selected_item is not None:
                add_to_map(self.qris_project, self.model, selected_item)

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
        item_type = model_item.data(item_code['item_type'])

        if item_type == 'project_root':
            self.menu.addAction('EXPAND_ALL', lambda: self.expand_tree())
            self.menu.addAction('COLLAPSE_ALL', lambda: self.collapse_tree())
        elif item_type == "extent_folder":
            self.menu.addAction('ADD_PROJECT_EXTENT_LAYER', lambda: self.import_project_extent_layer())
            self.menu.addAction('CREATE_BLANK_PROJECT_EXTENT_LAYER', lambda: self.create_blank_project_extent())
        elif item_type == "layers_folder":
            self.menu.addAction('IMPORT_PROJECT_LAYER', lambda: self.import_project_layer())
        elif item_type == "layer_node":
            self.menu.addAction('ADD_TO_MAP', lambda: add_to_map(self.qris_project, self.model, model_item))
        elif item_type in ['extent_node', 'Project_Extent']:
            self.menu.addAction('UPDATE_PROJECT_EXTENT', lambda: self.update_project_extent(model_item))
            self.menu.addAction('DELETE_PROJECT_EXTENT', lambda: self.delete_project_extent(model_item))
            self.menu.addAction('ADD_TO_MAP', lambda: add_to_map(self.qris_project, self.model, model_item))
        elif item_type == "design_folder":
            self.menu.addAction('ADD_DESIGN', lambda: self.add_design())
        elif item_type == "design":
            self.menu.addAction('ADD_TO_MAP', lambda: add_to_map(self.qris_project, self.model, model_item))
        elif item_type == "structure_type_folder":
            self.menu.addAction('ADD_STRUCTURE_TYPE', lambda: self.add_structure_type())
        elif item_type == "zoi_type_folder":
            self.menu.addAction('ADD_ZOI_TYPE', lambda: self.add_zoi_type())
        elif item_type == "zoi_type":
            self.menu.addAction('ADD_TO_MAP', lambda: add_to_map(self.qris_project, self.model, model_item))
        elif item_type == "phase_folder":
            self.menu.addAction('ADD_PHASE', lambda: self.add_phase())
        # elif item_type == "photos_folder":
        #     self.menu.addAction('IMPORT_PHOTOS', lambda: self.import_photos())
        #     self.menu.addAction('ADD_TO_MAP', lambda: add_to_map(self.qris_project, self.model, model_item))
        else:
            self.menu.clear()
        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def expand_tree(self):
        self.treeView.expandAll()
        return

    def collapse_tree(self):
        self.treeView.collapseAll()
        return

    def add_assessment(self):
        """Initiates adding a new assessment"""
        self.assessment_dialog = AssessmentDlg(self.qris_project)
        self.assessment_dialog.dateEdit_assessment_date.setDate(QDate.currentDate())
        self.assessment_dialog.dataChange.connect(self.build_tree_view)
        self.assessment_dialog.show()

    def add_design(self):
        """Initiates adding a new design"""
        self.design_dialog = DesignDlg(self.qris_project)
        # TODO remove this stuff about date
        self.design_dialog.dataChange.connect(self.build_tree_view)
        self.design_dialog.show()

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
            QMessageBox.information(self, "Structure Types", "Please create a new project design before adding structure types")

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

    def delete_project_extent(self, selected_item):
        """Deletes a project extent layer"""
        display_name = selected_item.data(item_code['INSTANCE']).display_name
        feature_name = selected_item.data(item_code['INSTANCE']).feature_name
        geopackage_path = selected_item.data(item_code['INSTANCE']).geopackage_path(self.qris_project.project_path)

        delete_ok = QMessageBox.question(self, f"Delete extent", f"Are you fucking sure you wanna delete the extent layer: {display_name}")
        if delete_ok == QMessageBox.Yes:
            # remove from the map if it's there
            # TODO consider doing this based on the path
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name() == display_name:
                    QgsProject.instance().removeMapLayers([layer.id()])
                    iface.mapCanvas().refresh()

            # TODO be sure to test whether the table exists first
            gdal_delete = gdal.OpenEx(geopackage_path, gdal.OF_UPDATE, allowed_drivers=['GPKG'])
            error = gdal_delete.DeleteLayer(feature_name)
            gdal_delete.ExecuteSQL('VACUUM')
            # TODO remove this from the Extents dictionary that will also remove from promect xml
            del(self.qris_project.project_extents[feature_name])
            # refresh the project xml
            self.qris_project.write_project_xml()
            # refresh the tree
            self.build_tree_view(self.qris_project, None)
        else:
            QMessageBox.information(self, "Delete extent", "No layers were deleted")

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
        raster = selected_item.data(item_code['INSTANCE'])
        self.elevation_widget = ElevationDockWidget(raster, self.qris_project)
        self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
        self.elevation_widget.dataChange.connect(self.build_tree_view)
        self.elevation_widget.show()
