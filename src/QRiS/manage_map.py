from optparse import Values
import os

from random import randint, randrange


from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsSymbol,
    QgsRendererCategory,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsSimpleFillSymbolLayer,
    QgsCategorizedSymbolRenderer,
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
    zoi_types_layer = QgsVectorLayer(geopackage_path + "|layername=zoi_types", "ZOI", "ogr")
    complexes_layer = QgsVectorLayer(geopackage_path + "|layername=complexes", "Complexes", "ogr")
    structure_points_layer = QgsVectorLayer(geopackage_path + "|layername=structure_points", "Structures", "ogr")
    structure_lines_layer = QgsVectorLayer(geopackage_path + "|layername=structure_lines", "Structures", "ogr")

    # Get the structure geometry type
    # Could also do this with SQL
    design_iterator = designs_layer.getFeatures(QgsFeatureRequest().setFilterFid(design_id))
    design_feature = next(design_iterator)
    structure_geometry = design_feature['structure_geometry']

    def add_design_table(display_name, table_name, qml_name, read_only, group_node):
        """A handy way to add design layers and tables to the map"""
        if not any([c.name() == display_name for c in group_node.children()]):
            layer = QgsProject.instance().addMapLayer(QgsVectorLayer(geopackage_path + "|layername=" + table_name, display_name, "ogr"), False)
            if qml_name:
                layer_qml = os.path.join(symbology_path, 'symbology', qml_name)
                layer.loadNamedStyle(layer_qml)
            if read_only:
                layer.setReadOnly()
            group_node.addLayer(layer)

    # Summary tables (views)
    if any([c.name() == "Low-Tech Tables" for c in node.children()]):
        # if is there set it to the design node
        table_node = next(n for n in node.children() if n.name() == "Low-Tech Tables")
    else:
        # if not add the node as a group
        table_node = node.addGroup("Low-Tech Tables")
        table_node.setExpanded(False)

    # Summary tables (views)
    if any([c.name() == "Summary Tables" for c in table_node.children()]):
        # if is there set it to the design node
        summary_node = next(n for n in table_node.children() if n.name() == "Summary Tables")
    else:
        # if not add the node as a group
        summary_node = table_node.addGroup("Summary Tables")
        summary_node.setExpanded(False)

    add_design_table('Structure Totals - Points', 'qry_total_structures_points', None, True, summary_node)
    add_design_table('Structure Totals - Lines', 'qry_total_structures_lines', None, True, summary_node)
    add_design_table('Structure Summary - Points', 'qry_structure_summary_points', None, True, summary_node)
    add_design_table('Structure Summary - Lines', 'qry_structure_summary_lines', None, True, summary_node)
    add_design_table('Complexes Summary - Points', 'qry_complexes_by_type_points', None, True, summary_node)
    add_design_table('Complexes Summary - Lines', 'qry_complexes_by_type_lines', None, True, summary_node)
    add_design_table('ZOI Summary', 'qry_zoi_summary', None, True, summary_node)

    # Lookup Tables
    if any([c.name() == "Lookup Tables" for c in table_node.children()]):
        # if is there set it to the design node
        lookup_node = next(n for n in table_node.children() if n.name() == "Lookup Tables")
    else:
        # if not add the node as a group
        lookup_node = table_node.addGroup("Lookup Tables")
        lookup_node.setExpanded(False)

    add_design_table('Design Status', 'lkp_design_status', 'lkp_design_status.qml', True, lookup_node)
    add_design_table('Phase Action', 'lkp_phase_action', 'lkp_phase_action.qml', True, lookup_node)
    add_design_table('ZOI Influence', 'lkp_zoi_influence', 'lkp_zoi_influence.qml', True, lookup_node)
    add_design_table('ZOI Stage', 'lkp_zoi_stage', 'lkp_zoi_stage.qml', True, lookup_node)
    add_design_table('Structure Mimics', 'lkp_structure_mimics', 'lkp_structure_mimics.qml', True, lookup_node)

    # Add Design Tables
    if any([c.name() == "Design Tables" for c in table_node.children()]):
        # if is there set it to the design node
        design_tables_node = next(n for n in table_node.children() if n.name() == "Design Tables")
    else:
        # if not add the node as a group
        design_tables_node = table_node.addGroup("Design Tables")
        design_tables_node.setExpanded(False)

    # Check if the designs table has been added and if not add it.
    add_design_table('Designs', 'designs', 'designs.qml', False, design_tables_node)
    add_design_table('Structure Types', 'structure_types', 'structure_types.qml', False, design_tables_node)
    add_design_table('ZOI Types', 'zoi_types', 'zoi_types.qml', False, design_tables_node)
    add_design_table('Phases', 'phases', 'phases.qml', False, design_tables_node)

    # Check if the design node is already added
    design_group_name = str(design_id) + "-" + item.text()
    if any([c.name() == design_group_name for c in node.children()]):
        # if is there set it to the design node
        design_node = next(n for n in node.children() if n.name() == design_group_name)
    else:
        # if not add the node as a group
        design_node = node.addGroup(design_group_name)

    # Add structures
    structure_layer_name = str(design_id) + "-Structures"
    if structure_geometry == 'Point':
        # Start setting custom symbology
        # TODO Refactor into a functio
        unique_values = []
        for feature in structure_types_layer.getFeatures():
            values = (feature["fid"], feature["name"])
            unique_values.append(values)
        categories = []
        for value in unique_values:
            layer_style = {}
            layer_style["color"] = '%d, %d, %d' % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
            layer_style['size'] = '3'
            layer_style['outline_color'] = 'black'
            symbol_layer = QgsMarkerSymbol.createSimple(layer_style)
            category = QgsRendererCategory(str(value[0]), symbol_layer, value[1])
            categories.append(category)
        renderer = QgsCategorizedSymbolRenderer('structure_type_id', categories)

        if not any([c.name() == structure_layer_name for c in design_node.children()]):
            # Adding the type suffix as I could see adding qml that symbolizes on other attributes
            structure_points_qml = os.path.join(symbology_path, 'symbology', 'structure_points.qml')
            structure_points_layer.loadNamedStyle(structure_points_qml)
            QgsExpressionContextUtils.setLayerVariable(structure_points_layer, 'parent_id', design_id)
            structure_points_layer.setSubsetString(subset_string)
            QgsProject.instance().addMapLayer(structure_points_layer, False)
            structure_points_layer.setName(structure_layer_name)
            design_node.addLayer(structure_points_layer)
            layer_node = design_node.findLayer(structure_points_layer.id())
            layer_node.setExpanded(False)
        else:
            structure_points_layer = QgsProject.instance().mapLayersByName(structure_layer_name)[0]
        if renderer is not None:
            structure_points_layer.setRenderer(renderer)
            structure_points_layer.triggerRepaint()

    else:
        # Add line structures
        # Start setting custom symbology
        # TODO Refactor into a function
        unique_values = []
        for feature in structure_types_layer.getFeatures():
            values = (feature["fid"], feature["name"])
            unique_values.append(values)

        categories = []
        for value in unique_values:
            layer_style = {}
            layer_style["color"] = '%d, %d, %d' % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
            layer_style['width'] = '1'
            layer_style['capstyle'] = 'round'
            symbol_layer = QgsLineSymbol.createSimple(layer_style)
            category = QgsRendererCategory(str(value[0]), symbol_layer, value[1])
            categories.append(category)
        renderer = QgsCategorizedSymbolRenderer('structure_type_id', categories)
        # end custom symbology

        if not any([c.name() == structure_layer_name for c in design_node.children()]):
            structures_lines_qml = os.path.join(symbology_path, 'symbology', 'structure_lines.qml')
            structure_lines_layer.loadNamedStyle(structures_lines_qml)
            QgsExpressionContextUtils.setLayerVariable(structure_lines_layer, 'parent_id', design_id)
            structure_lines_layer.setSubsetString(subset_string)
            QgsProject.instance().addMapLayer(structure_lines_layer, False)
            structure_lines_layer.setName(structure_layer_name)
            design_node.addLayer(structure_lines_layer)
            layer_node = design_node.findLayer(structure_lines_layer.id())
            layer_node.setExpanded(False)
        else:
            structure_lines_layer = QgsProject.instance().mapLayersByName(structure_layer_name)[0]
        if renderer is not None:
            structure_lines_layer.setRenderer(renderer)
            structure_lines_layer.triggerRepaint()

    # Add zoi
    zoi_layer_name = str(design_id) + "-ZOI"
    # TODO Refactor into a function
    # TODO Refactor into sql query
    unique_values = []
    for feature in zoi_types_layer.getFeatures():
        values = (feature["fid"], feature["name"])
        unique_values.append(values)
    categories = []
    for value in unique_values:
        layer_style = {}
        alpha = 60
        layer_style["color"] = "{}, {}, {}, {}".format(randrange(0, 256), randrange(0, 256), randrange(0, 256), alpha)
        layer_style["outline_width"] = '0.50'
        layer_style["outline_style"] = 'dash'
        symbol_layer = QgsFillSymbol.createSimple(layer_style)
        category = QgsRendererCategory(str(value[0]), symbol_layer, value[1])
        categories.append(category)
    renderer = QgsCategorizedSymbolRenderer('influence_type_id', categories)
    # End custom symbology

    # check for the zoi layer, and if it is not there symbolize and add it
    if not any([c.name() == zoi_layer_name for c in design_node.children()]):
        zoi_qml = os.path.join(symbology_path, 'symbology', 'zoi.qml')
        zoi_layer.loadNamedStyle(zoi_qml)
        QgsExpressionContextUtils.setLayerVariable(zoi_layer, 'parent_id', design_id)
        zoi_layer.setSubsetString(subset_string)
        QgsProject.instance().addMapLayer(zoi_layer, False)
        zoi_layer.setName(zoi_layer_name)
        design_node.addLayer(zoi_layer)
        layer_node = design_node.findLayer(zoi_layer.id())
        layer_node.setExpanded(False)
    else:
        zoi_layer = QgsProject.instance().mapLayersByName(zoi_layer_name)[0]
    if renderer is not None:
        zoi_layer.setRenderer(renderer)
    zoi_layer.triggerRepaint()

    # Add complexes
    complex_layer_name = str(design_id) + "-Complexes"
    if not any([c.name() == complex_layer_name for c in design_node.children()]):
        complex_qml = os.path.join(symbology_path, 'symbology', 'complexes.qml')
        complexes_layer.loadNamedStyle(complex_qml)
        QgsExpressionContextUtils.setLayerVariable(complexes_layer, 'parent_id', design_id)
        complexes_layer.setSubsetString(subset_string)
        QgsProject.instance().addMapLayer(complexes_layer, False)
        complexes_layer.setName(complex_layer_name)
        design_node.addLayer(complexes_layer)


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
