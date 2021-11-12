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
from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsExpressionContextUtils,
    QgsVectorFileWriter)

from qgis.gui import QgsDataSourceSelectDialog

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt, QDate
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon

from .classes.context_menu import ContextMenu
from .classes.settings import Settings

from .ui.elevation_dockwidget import ElevationDockWidget
from .ui.add_layer_dialog import AddLayerDlg
from .ui.add_detrended_dialog import AddDetrendedRasterDlg
from .ui.assessment_dialog import AssessmentDlg
from .ui.design_dialog import DesignDlg


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qris_dockwidget.ui'))

item_code = {'path': Qt.UserRole + 1,
             # specific for each type within the QRiS tree and determines which context menus are displayed
             'item_type': Qt.UserRole + 2,
             # LAYER - not too sure ideally this is redundent
             'LAYER': Qt.UserRole + 3,
             # map_layer usually refers to display within the QGIS layer tree often for groups
             'map_layer': Qt.UserRole + 4,
             # may be used to refer to a QML file
             'layer_symbology': Qt.UserRole + 5,
             # stores id within databases
             'feature_id': Qt.UserRole + 6}


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

    def open_project(self, qris_project, new_item=None):
        """Builds items in the tree view based on dictionary values that are part of the project"""
        # TODO resolve this naming - it is stupid and inconsistent throughout
        self.qris_project = qris_project

        self.model.clear()
        rootNode = self.model.invisibleRootItem()

        # set the projecr root
        project_node = QStandardItem(self.qris_project.project_name)
        project_node.setIcon(QIcon(':/plugins/qris_toolbar/test_Riverscapes.png'))
        project_node.setData('project_root', item_code['item_type'])
        project_node.setData('group', item_code['map_layer'])
        rootNode.appendRow(project_node)

        # Add project extent layers to tree
        project_extent_node = QStandardItem("Project Extents")
        project_extent_node.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
        project_extent_node.setData('project_extent_folder', item_code['item_type'])
        project_extent_node.setData('group', item_code['map_layer'])
        project_node.appendRow(project_extent_node)

        for layer in self.qris_project.project_extents.values():
            extent_node = QStandardItem(layer.name)
            extent_node.setIcon(QIcon(':/plugins/qris_toolbar/extent_polygon.png'))
            extent_node.setData(layer.type, item_code['item_type'])
            extent_node.setData('project_extent', item_code['map_layer'])
            extent_node.setData(layer, item_code['LAYER'])
            project_extent_node.appendRow(extent_node)

        # Add detrended rasters to tree
        detrended_rasters = QStandardItem("Detrended Rasters")
        detrended_rasters.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
        detrended_rasters.setData("DetrendedRastersFolder", item_code['item_type'])
        detrended_rasters.setData('group', item_code['map_layer'])
        project_node.appendRow(detrended_rasters)

        for raster in self.qris_project.detrended_rasters.values():
            detrended_raster = QStandardItem(raster.name)
            detrended_raster.setIcon(QIcon(':/plugins/qris_toolbar/qris_raster.png'))
            # detrended_raster.setData(raster.path, item_code['path'])
            detrended_raster.setData('DetrendedRaster', item_code['item_type'])
            detrended_raster.setData(raster, item_code['LAYER'])
            detrended_raster.setData('raster_layer', item_code['map_layer'])
            # detrended_raster.setData(os.path.join(os.path.dirname(__file__), "..", 'resources', 'symbology', 'hand.qml'), item_code['layer_symbology'])
            detrended_rasters.appendRow(detrended_raster)

            if len(raster.surfaces.values()) > 0:
                item_surfaces = QStandardItem("Surfaces")
                item_surfaces.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
                item_surfaces.setData('group', item_code['map_layer'])
                detrended_raster.appendRow(item_surfaces)
                for surface in raster.surfaces.values():
                    item_surface = QStandardItem(surface.name)
                    item_surface.setIcon(QIcon(':/plugins/qris_toolbar/layers/Polygon.png'))
                    # item_surface.setData(surface.path, item_code['path'])
                    item_surface.setData('DetrendedRasterSurface', item_code['item_type'])
                    item_surface.setData('surface_layer', item_code['map_layer'])
                    item_surface.setData(surface, item_code['LAYER'])
                    item_surfaces.appendRow(item_surface)

        # Add assessments to tree
        assessments_parent_node = QStandardItem("Riverscape Assessments")
        assessments_parent_node.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
        assessments_parent_node.setData('assessments_folder', item_code['item_type'])
        assessments_parent_node.setData('group', item_code['map_layer'])
        project_node.appendRow(assessments_parent_node)

        if self.qris_project.project_assessments:
            self.qris_project.assessments_path = os.path.join(self.qris_project.project_path, "Assessments.gpkg")
            assessments_layer = QgsVectorLayer(self.qris_project.assessments_path + "|layername=assessments", "assessments", "ogr")
            for assessment_feature in assessments_layer.getFeatures():
                assessment_node = QStandardItem(assessment_feature.attribute('assessment_date').toString('yyyy-MM-dd'))
                assessment_node.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
                assessment_node.setData('dam_assessment', item_code['item_type'])
                assessment_node.setData('group', item_code['map_layer'])
                assessment_node.setData(assessment_feature.attribute('fid'), item_code['feature_id'])
                assessments_parent_node.appendRow(assessment_node)

        assessments_parent_node.sortChildren(Qt.AscendingOrder)

        # Add designs to tree
        designs_parent_node = QStandardItem("Low-Tech Designs")
        designs_parent_node.setIcon(QIcon(':/plugins/qris_toolbar/folder.png'))
        designs_parent_node.setData('DesignsFolder', item_code['item_type'])
        designs_parent_node.setData('group', item_code['map_layer'])
        project_node.appendRow(designs_parent_node)

        if self.qris_project.project_designs:
            self.qris_project.designs_path = os.path.join(self.qris_project.project_path, "Designs.gpkg")
            designs_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=designs", "designs", "ogr")
            for design_feature in designs_layer.getFeatures():
                design_node = QStandardItem(design_feature.attribute('design_name'))
                design_node.setIcon(QIcon(':/plugins/qris_toolbar/qris_design.png'))
                design_node.setData('design', item_code['item_type'])
                design_node.setData('group', item_code['map_layer'])
                design_node.setData(design_feature.attribute('fid'), item_code['feature_id'])
                designs_parent_node.appendRow(design_node)

        designs_parent_node.sortChildren(Qt.AscendingOrder)

        # Check if new item is in the tree, if it is pass it to the new_item function
        if new_item is not None:
            selected_item = self._find_item_in_model(new_item)
            if selected_item is not None:
                self.add_to_map(selected_item)

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

        item = self.model.itemFromIndex(indexes[0])
        # project_tree_data = item.data(Qt.UserRole)  # ProjectTreeData object
        # data = project_tree_data.data  # Could be a QRaveBaseMap, a QRaveMapLayer or just some random data
        # connect signals to treeView menu items
        item_type = item.data(item_code['item_type'])
        if item_type == 'project_root':
            self.menu.addAction('EXPAND_ALL', lambda: self.expand_all())
        elif item_type == "project_extent_folder":
            self.menu.addAction('ADD_PROJECT_EXTENT_LAYER', lambda: self.import_project_extent_layer())
            self.menu.addAction('CREATE_BLANK_PROJECT_EXTENT_LAYER', lambda: self.create_blank_project_extent())
        elif item_type == "DetrendedRastersFolder":
            self.menu.addAction('ADD_DETRENDED_RASTER', lambda: self.add_detrended_raster())
        elif item_type == "DetrendedRaster":
            self.menu.addAction('EXPLORE_ELEVATIONS', lambda: self.explore_elevations(item))
            self.menu.addAction('ADD_TO_MAP', lambda: self.add_to_map(item))
        elif item_type in ["DetrendedRasterSurface", 'project_extent', 'Project_Extent', "dam_assessment", "design"]:
            self.menu.addAction('ADD_TO_MAP', lambda: self.add_to_map(item))
        elif item_type == "assessments_folder":
            self.menu.addAction('ADD_ASSESSMENT', lambda: self.add_assessment())
        elif item_type == "DesignsFolder":
            self.menu.addAction('ADD_DESIGN', lambda: self.add_design())
        else:
            self.menu.clear()
        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_assessment(self):
        """Initiates adding a new assessment"""
        self.assessment_dialog = AssessmentDlg(self.qris_project)
        self.assessment_dialog.dateEdit_assessment_date.setDate(QDate.currentDate())
        self.assessment_dialog.dataChange.connect(self.open_project)
        self.assessment_dialog.show()

    def add_design(self):
        """Initiates adding a new design"""
        self.design_dialog = DesignDlg(self.qris_project)
        # TODO remove this stuff about date
        self.design_dialog.dataChange.connect(self.open_project)
        self.design_dialog.show()

    def add_detrended_raster(self):
        # last_browse_path = self.settings.getValue('lastBrowsePath')
        # last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None
        dialog_return = QFileDialog.getOpenFileName(None, "Add Detrended Raster to QRiS project", None, self.tr("Raster Data Sources (*.tif)"))
        if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
            self.addDetrendedDlg = AddDetrendedRasterDlg(None, dialog_return[0], self.qris_project)
            self.addDetrendedDlg.dataChange.connect(self.open_project)
            self.addDetrendedDlg.exec()

    def import_project_extent_layer(self):
        """launches the dialog that supports import of project layers"""
        select_layer = QgsDataSourceSelectDialog()
        select_layer.exec()
        uri = select_layer.uri()
        if uri is not None and uri.isValid() and uri.wkbType == 3:
            self.addProjectLayerDlg = AddLayerDlg(uri, self.qris_project)
            self.addProjectLayerDlg.dataChange.connect(self.open_project)
            self.addProjectLayerDlg.exec_()
        else:
            QMessageBox.critical(self, "Invalid Layer", "Please select a valid polygon spatial data layer")

    def create_blank_project_extent(self):
        """Adds a blank project extent that will be edited by the user"""
        self.addProjectLayerDlg = AddLayerDlg(None, self.qris_project)
        self.addProjectLayerDlg.dataChange.connect(self.open_project)
        self.addProjectLayerDlg.exec_()

    def explore_elevations(self, selected_item):
        raster = selected_item.data(item_code['LAYER'])
        self.elevation_widget = ElevationDockWidget(raster, self.qris_project)
        self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
        self.elevation_widget.dataChange.connect(self.open_project)
        self.elevation_widget.show()

    def add_to_map(self, selected_item):
        """Adds selected items from the QRiS tree to the QGIS layer tree and also to the map"""
        # TODO consider giving node a more explicit name
        node = QgsProject.instance().layerTreeRoot()
        parents = self._get_parents(selected_item)
        parents.append(selected_item)
        # for each parent node
        for item in parents:
            # if has the code group
            if item.data(item_code['map_layer']) == 'group':
                # check if the group is in the qgis layer tree
                if any([c.name() == item.text() for c in node.children()]):
                    # if is set it to the active node
                    node = next(n for n in node.children() if n.name() == item.text())
                else:
                    # if not add the group as a node
                    new_node = node.addGroup(item.text())
                    node = new_node
                    # Check the type and launch an add to map function
                    if (item.data(item_code['item_type']) == 'design'):
                        self.add_design_to_map(item, node)
                    elif (item.data(item_code['item_type']) == 'dam_assessment'):
                        self.add_assessment_to_map(item, node)
            # TODO refactor these into their own functions - someday
            # if it's not a group map_layer, but is a raster layer
            elif item.data(item_code['map_layer']) == 'raster_layer':
                # check if the layer text is in the layer tree already
                if not any([c.name() == item.text() for c in node.children()]):
                    # if not start set the raster as a layer
                    layer = QgsRasterLayer(os.path.join(self.qris_project.project_path, item.data(item_code['LAYER']).path), item.text())
                    # TODO load a qml for raster style
                    layer.loadNamedStyle(item.data(item_code['layer_symbology']))
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)
            elif item.data(item_code['map_layer']) in ['surface_layer', 'project_extent']:
                if not any([c.name() == item.text() for c in node.children()]):
                    layer = QgsVectorLayer(f"{os.path.join(self.qris_project.project_path, os.path.dirname(item.data(item_code['LAYER']).path))}|layername={os.path.basename(item.data(item_code['LAYER']).path)}",
                                           item.text(), 'ogr')
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)

    def add_assessment_to_map(self, item, node):
        """adds assessments to the map"""
        assessment_id = item.data(item_code['feature_id'])
        layer = QgsVectorLayer(self.qris_project.assessments_path + "|layername=dams", "Dams-" + item.text(), "ogr")
        layer.setSubsetString("assessment_id = " + str(assessment_id))
        QgsExpressionContextUtils.setLayerVariable(layer, 'parent_id', assessment_id)
        symbology_path = os.path.join(os.path.dirname(__file__), 'symbology', 'assessments_dams.qml')
        layer.loadNamedStyle(symbology_path)
        QgsProject.instance().addMapLayer(layer, False)
        node.addLayer(layer)

    def add_design_to_map(self, item, node):
        """adds designs to the map"""
        design_id = item.data(item_code['feature_id'])
        design_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=designs", "designs", "ogr")
        structure_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=structures", "Structures-" + str(design_id), "ogr")
        complex_layer = QgsVectorLayer(self.qris_project.designs_path + "|layername=complexes", "Complexes-" + str(design_id), "ogr")
        structure_layer.setSubsetString("design_id = " + str(design_id))
        complex_layer.setSubsetString("design_id = " + str(design_id))
        structure_symbology_path = os.path.join(os.path.dirname(__file__), 'symbology', 'designs_structures.qml')
        complex_symbology_path = os.path.join(os.path.dirname(__file__), 'symbology', 'designs_complexes.qml')
        structure_layer.loadNamedStyle(structure_symbology_path)
        complex_layer.loadNamedStyle(complex_symbology_path)
        QgsExpressionContextUtils.setLayerVariable(structure_layer, 'parent_id', design_id)
        QgsExpressionContextUtils.setLayerVariable(complex_layer, 'parent_id', design_id)
        QgsProject.instance().addMapLayer(structure_layer, False)
        QgsProject.instance().addMapLayer(complex_layer, False)
        node.addLayer(structure_layer)
        node.addLayer(complex_layer)

    def expand_all(self):
        self.treeView.expand_all()
        return

    def _get_parents(self, start_item: QStandardItem):
        """This gets a """
        parents = []
        placeholder = start_item.parent()
        while placeholder is not None and placeholder != self.model.invisibleRootItem():
            parents.append(placeholder)
            placeholder = placeholder.parent()
        parents.reverse()
        return parents

    def _find_item_in_model(self, name):
        """Looks in the tree for an item name passed from the dataChange method."""
        selected_item = self.model.findItems(name, Qt.MatchRecursive)[0]
        return selected_item
