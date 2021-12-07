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
        if item_type == 'project_extent':
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
    # TODO be sure to add the appropriate
    # TODO be sure that you are not adding things twice. i.e., check if each layer exists before adding.
    """adds designs to the map"""
    design_id = item.data(item_code['feature_id'])
    structure_layer = QgsVectorLayer(qris_project.designs_path + "|layername=structures", "Structures-" + str(design_id), "ogr")
    complex_layer = QgsVectorLayer(qris_project.designs_path + "|layername=complexes", "Complexes-" + str(design_id), "ogr")
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
