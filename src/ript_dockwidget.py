# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RIPTDockWidget
                                 A QGIS plugin
 Riverscapes Integrated Planning Tool (RIPT)
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
    QgsVectorFileWriter)

from qgis.gui import QgsDataSourceSelectDialog

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon

from .classes.context_menu import ContextMenu
from .ript_elevation_dockwidget import RIPTElevationDockWidget
from .add_detrended_dialog import AddDetrendedRasterDlg
from .add_layer_dialog import AddLayerDlg
from .classes.settings import Settings

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_dockwidget_base.ui'))

item_code = {'path': Qt.UserRole + 1,
             'item_type': Qt.UserRole + 2,
             'LAYER': Qt.UserRole + 3,
             'map_layer': Qt.UserRole + 4,
             'layer_symbology': Qt.UserRole + 5}


class RIPTDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RIPTDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.settings = Settings()

        self.current_project = None
        self.menu = ContextMenu()

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)

        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

    def openProject(self, ript_project, add_to_map=None):

        self.current_project = ript_project

        self.model.clear()
        rootNode = self.model.invisibleRootItem()

        ript_name = QStandardItem(ript_project.project_name)
        ript_name.setIcon(QIcon(':/plugins/ript_toolbar/RaveAddIn_16px.png'))
        ript_name.setData('project_root', item_code['item_type'])
        ript_name.setData('group', item_code['map_layer'])
        rootNode.appendRow(ript_name)

        # Add detrended rasters to tree
        detrended_rasters = QStandardItem("Detrended Rasters")
        detrended_rasters.setIcon(QIcon(':/plugins/ript_toolbar/BrowseFolder.png'))
        detrended_rasters.setData("DetrendedRastersFolder", item_code['item_type'])
        detrended_rasters.setData('group', item_code['map_layer'])
        ript_name.appendRow(detrended_rasters)

        for raster in ript_project.detrended_rasters.values():
            detrended_raster = QStandardItem(raster.name)
            detrended_raster.setIcon(QIcon(':/plugins/ript_toolbar/layers/Raster.png'))
            # detrended_raster.setData(raster.path, item_code['path'])
            detrended_raster.setData('DetrendedRaster', item_code['item_type'])
            detrended_raster.setData(raster, item_code['LAYER'])
            detrended_raster.setData('raster_layer', item_code['map_layer'])
            detrended_raster.setData(os.path.join(os.path.dirname(__file__), "..", 'resources', 'symbology', 'hand.qml'), item_code['layer_symbology'])
            detrended_rasters.appendRow(detrended_raster)

            if len(raster.surfaces.values()) > 0:
                item_surfaces = QStandardItem("Surfaces")
                item_surfaces.setIcon(QIcon(':/plugins/ript_toolbar/BrowseFolder.png'))
                item_surfaces.setData('group', item_code['map_layer'])
                detrended_raster.appendRow(item_surfaces)
                for surface in raster.surfaces.values():
                    item_surface = QStandardItem(surface.name)
                    item_surface.setIcon(QIcon(':/plugins/ript_toolbar/layers/Polygon.png'))
                    # item_surface.setData(surface.path, item_code['path'])
                    item_surface.setData('DetrendedRasterSurface', item_code['item_type'])
                    item_surface.setData('surface_layer', item_code['map_layer'])
                    item_surface.setData(surface, item_code['LAYER'])
                    item_surfaces.appendRow(item_surface)

        # Add project layers to tree
        project_layers = QStandardItem("Project Layers")
        project_layers.setIcon(QIcon(':/plugins/ript_toolbar/BrowseFolder.png'))
        project_layers.setData('ProjectLayersFolder', item_code['item_type'])
        ript_name.appendRow(project_layers)

        for project_layer in ript_project.project_layers.values():
            layer = QStandardItem(project_layer.name)
            # layer.setData(project_layer.path, item_code['path'])
            layer.setData(project_layer.type, item_code['item_type'])
            layer.setData('project_layer', item_code['map_layer'])
            layer.setData(project_layer, item_code['LAYER'])
            project_layers.appendRow(layer)

        # Add assessments to tree
        assessment_layers = QStandardItem("Riverscape Assessments")
        assessment_layers.setIcon(QIcon(':/plugins/ript_toolbar/BrowseFolder.png'))
        assessment_layers.setData('AssessmentLayersFolder', item_code['item_type'])
        ript_name.appendRow(assessment_layers)

        if add_to_map is not None:
            selected_item = self._findItemInModel(add_to_map)
            if selected_item is not None:
                self.addToMap(selected_item)

    def closeEvent(self, event):
        self.current_project = None
        self.closingPlugin.emit()
        event.accept()

    def open_menu(self, position):

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
            self.menu.addAction('EXPAND_ALL', lambda: self.expandAll())
        elif item_type == "DetrendedRastersFolder":
            self.menu.addAction('ADD_DETRENDED_RASTER', lambda: self.addDetrendedRasterToProject())
        elif item_type == "DetrendedRaster":
            self.menu.addAction('EXPLORE_ELEVATIONS', lambda: self.exploreElevations(item))
            self.menu.addAction('ADD_TO_MAP', lambda: self.addToMap(item))
        elif item_type in ["DetrendedRasterSurface", 'project_layer', "Project_Extent"]:
            self.menu.addAction('ADD_TO_MAP', lambda: self.addToMap(item))
        elif item_type == "ProjectLayersFolder":
            self.menu.addAction('ADD_PROJECT_LAYER', lambda: self.addLayerToProject())
        elif item_type == "AssessmentLayersFolder":
            self.menu.addAction('BEGIN_NEW_ASSESSMENT', lambda: self.addAssessments())
        else:
            self.menu.clear()

        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def addAssessments(self):
        # TODO someday integrate with a remote PostGIS DB.
        # create a geopackage
        assessment_path = os.path.join(self.current_project.project_path, "Assessments.gpkg")
        if not os.path.exists(assessment_path):
            # TODO this should not be a point layer, refactor to a table without geometry
            assessments_layer = QgsVectorLayer("point", "assessments_layer", "memory")
            # write to disk
            QgsVectorFileWriter.writeAsVectorFormat(assessments_layer, assessment_path, 'utf-8', driverName='GPKG', onlySelected=False)

            # Add JAM layer
            # TODO flesh out attribute data model
            jam_layer_uri = "point?crs=EPSG:4326&field=type:string&wood_count:string&index=yes"
            # create the layer in memory from the uri
            jam_layer_memory = QgsVectorLayer(jam_layer_uri, "jams", "memory")

            # setup the addition to the assessment geopackage
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = "jams"
            options.driverName = 'GPKG'
            if os.path.exists(assessment_path):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(
                jam_layer_memory, assessment_path, options)

            # Add DAM layer
            # TODO flesh out attribute data model
            dam_layer_uri = "point?crs=EPSG:4326&field=type:string&dam_count:string&index=yes"
            # create the layer in memory from the uri
            dam_layer_memory = QgsVectorLayer(dam_layer_uri, "dams", "memory")

            # setup the addition to the assessment geopackage
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = "dams"
            options.driverName = 'GPKG'
            if os.path.exists(assessment_path):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            QgsVectorFileWriter.writeAsVectorFormat(
                dam_layer_memory, assessment_path, options)

            # TODO add layer for geomorphic survey

            # TODO add layers to QRiS tree view

    def addDetrendedRasterToProject(self):

        # last_browse_path = self.settings.getValue('lastBrowsePath')
        # last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None

        dialog_return = QFileDialog.getOpenFileName(None, "Add Detrended Raster to QRiS project", None, self.tr("Raster Data Sources (*.tif)"))
        if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
            self.addDetrendedDlg = AddDetrendedRasterDlg(None, dialog_return[0], self.current_project)
            self.addDetrendedDlg.dataChange.connect(self.openProject)
            self.addDetrendedDlg.exec()

    def addLayerToProject(self):

        select_layer = QgsDataSourceSelectDialog()
        select_layer.exec()
        uri = select_layer.uri()
        if uri is not None and uri.isValid():  # check for polygon
            self.addProjectLayerDlg = AddLayerDlg(uri, self.current_project)
            self.addProjectLayerDlg.dataChange.connect(self.openProject)
            self.addProjectLayerDlg.exec_()

    def exploreElevations(self, selected_item):

        raster = selected_item.data(item_code['LAYER'])
        self.elevation_widget = RIPTElevationDockWidget(raster, self.current_project)
        self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
        self.elevation_widget.dataChange.connect(self.openProject)
        self.elevation_widget.show()

    def addToMap(self, selected_item):

        node = QgsProject.instance().layerTreeRoot()
        tree = self._get_parents(selected_item)
        tree.append(selected_item)
        for item in tree:
            if item.data(item_code['map_layer']) == 'group':
                if any([c.name() == item.text() for c in node.children()]):
                    node = next(n for n in node.children() if n.name() == item.text())
                else:
                    new_node = node.addGroup(item.text())
                    node = new_node
            elif item.data(item_code['map_layer']) == 'raster_layer':
                if not any([c.name() == item.text() for c in node.children()]):
                    layer = QgsRasterLayer(os.path.join(self.current_project.project_path, item.data(item_code['LAYER']).path), item.text())
                    layer.loadNamedStyle(item.data(item_code['layer_symbology']))
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)
            elif item.data(item_code['map_layer']) in ['surface_layer', 'project_layer']:
                if not any([c.name() == item.text() for c in node.children()]):
                    layer = QgsVectorLayer(f"{os.path.join(self.current_project.project_path, os.path.dirname(item.data(item_code['LAYER']).path))}|layername={os.path.basename(item.data(item_code['LAYER']).path)}",
                                           item.text(), 'ogr')
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)
            else:
                pass

    def expandAll(self):
        self.treeView.expandAll()
        return

    def _get_parents(self, start_item: QStandardItem):
        stack = []
        placeholder = start_item.parent()
        while placeholder is not None and placeholder != self.model.invisibleRootItem():
            stack.append(placeholder)
            placeholder = placeholder.parent()
        stack.reverse()
        return stack

    def _findItemInModel(self, name):
        selected_item = self.model.findItems(name, Qt.MatchRecursive)[0]
        return selected_item
