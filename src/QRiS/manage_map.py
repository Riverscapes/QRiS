import os

from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsExpressionContextUtils)

from qgis.PyQt.QtGui import QStandardItem
from qgis.PyQt.QtCore import Qt

from ..QRiS.qt_user_role import item_code


def add_to_map(qris_project, model, selected_item):
    """
    Adds selected items from the QRiS tree to the QGIS layer tree and also to the map
    model: is the QStandardItem model used to construct the QRiS tree view
    selected_item: is the item selected from the QRiS tree view
    """
    node = QgsProject.instance().layerTreeRoot()
    parents = _get_parents(model, selected_item)
    parents.append(selected_item)
    # for each node in parent
    for item in parents:
        # TODO I don't think we will need item_layer. just item_type
        item_type = item.data(item_code['item_type'])
        # Check the item_type and launch specific add to map function
        if item_type == 'extent_node':
            add_project_extent_to_map(qris_project, item, node)
        elif item_type == 'design':
            add_design_to_map(qris_project, item, node)
        # elif item_type == 'dam_assessment':
        #     add_assessment_to_map(item, node)
        # Check if it is a node that is already there
        elif any([c.name() == item.text() for c in node.children()]):
            # if is there set it to the next active node and search the next item
            node = next(n for n in node.children() if n.name() == item.text())
        else:
            # if not add the node as a group
            new_node = node.addGroup(item.text())
            # and set it as next active search node
            node = new_node


def _get_parents(model, start_item: QStandardItem):
    """This gets all the parent folder items of a selected item in the QRiS tree and passess them back to the add_to_map function"""
    parents = []
    placeholder = start_item.parent()
    while placeholder is not None and placeholder != model.invisibleRootItem():
        parents.append(placeholder)
        placeholder = placeholder.parent()
    parents.reverse()
    return parents


def add_project_extent_to_map(qris_project, item, node):
    """adds a project extent to the project extent node"""
    # check if it's already a child of the parent node and add it if not
    if not any([c.name() == item.text() for c in node.children()]):
        # if not just crate the path and then add it
        full_path = item.data(item_code['INSTANCE']).full_path(qris_project.project_path)
        layer = QgsVectorLayer(full_path, item.text(), 'ogr')
        QgsProject.instance().addMapLayer(layer, False)
        # TODO add symbology
        node.addLayer(layer)


# def add_assessment_to_map(item, node):
#     """adds assessments to the map"""
#     assessment_id = item.data(item_code['feature_id'])
#     layer = QgsVectorLayer(self.qris_project.assessments_path + "|layername=dams", "Dams-" + item.text(), "ogr")
#     layer.setSubsetString("assessment_id = " + str(assessment_id))
#     QgsExpressionContextUtils.setLayerVariable(layer, 'parent_id', assessment_id)
#     symbology_path = os.path.join(os.path.dirname(__file__), 'symbology', 'assessments_dams.qml')
#     layer.loadNamedStyle(symbology_path)
#     QgsProject.instance().addMapLayer(layer, False)
#     node.addLayer(layer)


def add_design_to_map(qris_project, item, node):
    """adds designs to the map"""
    # Establish paths to layers
    design_id = item.data(item_code['feature_id'])
    design_name = item.text()
    geopackage_path = qris_project.project_designs.geopackage_path(qris_project.project_path)

    designs_layer = QgsVectorLayer(geopackage_path + "|layername=designs", "Designs", "ogr")
    structure_types_layer = QgsVectorLayer(geopackage_path + "|layername=structure_types", "Structure Types", "ogr")
    zoi_layer = QgsVectorLayer(geopackage_path + "|layername=structure_zoi", "ZOI", "ogr")
    structures_field_layer = QgsVectorLayer(geopackage_path + "|layername=structures_field", "Field Structures", "ogr")
    structures_desktop_layer = QgsVectorLayer(geopackage_path + "|layername=structures_desktop", "Desktop Structures", "ogr")

    # TODO check if the structure types table has been added and if not add it.
    if not any([c.name() == 'Structure Types' for c in node.children()]):
        QgsProject.instance().addMapLayer(structure_types_layer, False)
        # TODO consider making the types read only
        node.addLayer(structure_types_layer)
        # TODO check the type of project design and add the project type field vs desktop
        # Check if the low tech design node is already added
    if any([c.name() == item.text() for c in node.children()]):
        # if is there set it to the design node
        design_node = next(n for n in node.children() if n.name() == item.text())
    else:
        # if not add the node as a group
        design_node = node.addGroup(item.text())

    # TODO Consider only adding the field or design table to each design

    zoi_qml = os.path.join(os.path.dirname(__file__), 'symbology', 'designs_zoi.qml')
    structures_field_qml = os.path.join(os.path.dirname(__file__), 'symbology', 'designs_structures_field.qml')
    structures_desktop_qml = os.path.join(os.path.dirname(__file__), 'symbology', 'designs_structures_desktop.qml')
    # zoi_layer.loadNamedStyle(zoi_qml)
    structures_field_layer.loadNamedStyle(structures_field_qml)
    # structures_field_layer.loadNamedStyle(structures_desktop_qml)

    QgsExpressionContextUtils.setLayerVariable(structures_field_layer, 'parent_id', design_id)
    QgsExpressionContextUtils.setLayerVariable(structures_desktop_layer, 'parent_id', design_id)
    QgsExpressionContextUtils.setLayerVariable(zoi_layer, 'parent_id', design_id)

    subset_string = ("design_id = " + str(design_id))
    zoi_layer.setSubsetString(subset_string)
    structures_field_layer.setSubsetString(subset_string)
    structures_desktop_layer.setSubsetString(subset_string)

    QgsProject.instance().addMapLayer(structures_field_layer, False)
    QgsProject.instance().addMapLayer(structures_desktop_layer, False)
    QgsProject.instance().addMapLayer(zoi_layer, False)
    design_node.addLayer(structures_field_layer)
    design_node.addLayer(structures_desktop_layer)
    design_node.addLayer(zoi_layer)
