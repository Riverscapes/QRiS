import os

from random import randint


from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsProject,
    QgsExpressionContextUtils)

from qgis.PyQt.QtGui import QStandardItem, QColor
from qgis.PyQt.QtCore import Qt

from ..QRiS.qt_user_role import item_code

# path to symbology directory
symbology_path = os.path.dirname(os.path.dirname(__file__))


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
        if item_type == 'layer_node':
            add_layer_to_map(qris_project, item, node)
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
        extent_qml = os.path.join(symbology_path, 'symbology', 'project_extent.qml')
        layer.loadNamedStyle(extent_qml)
        # Randomize the symbology outline color on add
        random_color = QColor(randint(1, 255), randint(1, 255), randint(1, 255))
        layer.renderer().symbol().symbolLayer(0).setStrokeColor(random_color)
        # Add the layer
        node.addLayer(layer)


def add_design_to_map(qris_project, item, node):
    """adds designs to the map"""
    # Establish paths to layers
    design_id = item.data(item_code['feature_id'])
    subset_string = ("design_id = " + str(design_id))
    design_name = item.text()
    geopackage_path = qris_project.project_designs.geopackage_path(qris_project.project_path)

    designs_layer = QgsVectorLayer(geopackage_path + "|layername=designs", "Designs", "ogr")
    structure_types_layer = QgsVectorLayer(geopackage_path + "|layername=structure_types", "Structure Types", "ogr")
    phases_layer = QgsVectorLayer(geopackage_path + "|layername=phases", "Implementation Phases", "ogr")
    zoi_layer = QgsVectorLayer(geopackage_path + "|layername=zoi", "ZOI", "ogr")
    footprints_layer = QgsVectorLayer(geopackage_path + "|layername=footprints", "Footprints", "ogr")
    structure_points_layer = QgsVectorLayer(geopackage_path + "|layername=structure_points", "Structures", "ogr")
    structure_lines_layer = QgsVectorLayer(geopackage_path + "|layername=structure_lines", "Structures", "ogr")

    # Get the design source as field or desktop from the feature itself
    design_iterator = designs_layer.getFeatures(QgsFeatureRequest().setFilterFid(design_id))
    design_feature = next(design_iterator)
    design_geometry = design_feature['design_geometry']

    # Check if the designs table has been added and if not add it.
    if not any([c.name() == 'Designs' for c in node.children()]):
        QgsProject.instance().addMapLayer(designs_layer, False)
        # TODO consider making the types read only
        node.addLayer(designs_layer)
        # Consider making this layer read only

    # Check if the structure types table has been added and if not add it.
    if not any([c.name() == 'Structure Types' for c in node.children()]):
        QgsProject.instance().addMapLayer(structure_types_layer, False)
        # TODO consider making the types read only
        node.addLayer(structure_types_layer)
        # Consider making this layer read only

    # Check if the Phases table has been added and if not add it.
    if not any([c.name() == 'Implementation Phases' for c in node.children()]):
        QgsProject.instance().addMapLayer(phases_layer, False)
        # Add the qml
        phase_qml = os.path.join(symbology_path, 'symbology', 'phases.qml')
        phases_layer.loadNamedStyle(phase_qml)
        node.addLayer(phases_layer)
        # Consider making this layer read only

    # Check if the low tech design node is already added
    if any([c.name() == item.text() for c in node.children()]):
        # if is there set it to the design node
        design_node = next(n for n in node.children() if n.name() == item.text())
    else:
        # if not add the node as a group
        design_node = node.addGroup(item.text())

    # TODO All layers consider adding symbology that randomizes some aspect of colors for differentiation
    # TODO All layers consider adding a design identifier such as the fid to the filtered layer name
    if design_geometry == 'Point':
        # Add point structures
        if not any([c.name() == 'Structures' for c in design_node.children()]):
            # Adding the type suffix as I could see adding qml that symbolizes on other attributes
            structure_points_type_qml = os.path.join(symbology_path, 'symbology', 'structure_points_type.qml')
            structure_points_layer.loadNamedStyle(structure_points_type_qml)
            QgsExpressionContextUtils.setLayerVariable(structure_points_layer, 'parent_id', design_id)
            structure_points_layer.setSubsetString(subset_string)
            QgsProject.instance().addMapLayer(structure_points_layer, False)
            design_node.addLayer(structure_points_layer)
    else:
        # Add line structures
        if not any([c.name() == 'Structures' for c in design_node.children()]):
            structures_desktop_qml = os.path.join(symbology_path, 'symbology', 'structure_lines.qml')
            structure_lines_layer.loadNamedStyle(structures_desktop_qml)
            QgsExpressionContextUtils.setLayerVariable(structure_lines_layer, 'parent_id', design_id)
            structure_lines_layer.setSubsetString(subset_string)
            QgsProject.instance().addMapLayer(structure_lines_layer, False)
            design_node.addLayer(structure_lines_layer)

    # Add zoi
    if not any([c.name() == 'ZOI' for c in design_node.children()]):
        zoi_qml = os.path.join(symbology_path, 'symbology', 'designs_zoi.qml')
        zoi_layer.loadNamedStyle(zoi_qml)
        QgsExpressionContextUtils.setLayerVariable(zoi_layer, 'parent_id', design_id)
        zoi_layer.setSubsetString(subset_string)
        QgsProject.instance().addMapLayer(zoi_layer, False)
        design_node.addLayer(zoi_layer)

    # Add footprints
    if not any([c.name() == 'Footprints' for c in design_node.children()]):
        # zoi_qml = os.path.join(symbology_path, 'symbology', 'designs_zoi.qml')
        # zoi_layer.loadNamedStyle(zoi_qml)
        QgsExpressionContextUtils.setLayerVariable(footprints_layer, 'parent_id', design_id)
        footprints_layer.setSubsetString(subset_string)
        QgsProject.instance().addMapLayer(footprints_layer, False)
        design_node.addLayer(footprints_layer)


def add_layer_to_map(qris_project, item, node):
    """adds a clipped project vector layer to the map"""
    # check if it's already a child of the parent node and add it if not
    if not any([c.name() == item.text() for c in node.children()]):
        # if not just create the path and then add it
        full_path = item.data(item_code['INSTANCE']).full_path(qris_project.project_path)
        layer = QgsVectorLayer(full_path, item.text(), 'ogr')
        QgsProject.instance().addMapLayer(layer, False)
        # TODO add symbology probably based on geometry type
        node.addLayer(layer)
