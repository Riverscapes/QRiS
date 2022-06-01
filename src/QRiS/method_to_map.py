from email.mime import base
from locale import CODESET
import os
import sqlite3

from random import randint, randrange
from urllib.parse import non_hierarchical


from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsField,
    QgsLayerTreeGroup,
    QgsLayerTreeNode,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsLayerTree,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsMapLayer,
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
from qgis.PyQt.QtCore import Qt, QVariant

from ..model.assessment import ASSESSMENT_MACHINE_CODE, Assessment
from ..model.mask import MASK_MACHINE_CODE, Mask
from ..model.basemap import BASEMAP_MACHINE_CODE, Basemap


from ..model.db_item import DBItem, dict_factory
from ..model.mask import Mask
from ..model.basemap import BASEMAP_MACHINE_CODE, Basemap
from ..model.project import Project, PROJECT_MACHINE_CODE

# path to symbology directory
symbology_path = os.path.dirname(os.path.dirname(__file__))

# TODO consider moving this somewhere more universal for use in other modules

QRIS_MAP_LAYER_MACHINE_CODE = 'QRIS_MAP_LAYER_MACHINE_CODE'


def get_db_item_layer(db_item: DBItem, layer: QgsLayerTreeNode) -> QgsLayerTreeNode:
    """
    Finds the tree item that represents the db_item. Returns None if it cannot be found.
    The function first checks if the layer argument represents db_item
    and then recursively searches all of the children of layer.

    layer should either be the QRiS project node, or a node within the project.
    """

    # Check whether the node that was passed in possesses the correct custom property
    custom_property = layer.customProperty(QRIS_MAP_LAYER_MACHINE_CODE)
    if isinstance(custom_property, DBItem) and db_item == custom_property:
        return layer

    # If the layer is a group then search it's children
    if isinstance(layer, QgsLayerTreeGroup):
        for child_layer in layer.children():
            result = get_db_item_layer(db_item, child_layer)
            if isinstance(result, QgsLayerTreeNode):
                return result

    return None


def get_group_layer(machine_code, group_label, parent: QgsLayerTreeGroup, add_missing=False) -> QgsLayerTreeGroup:
    """
    Finds a group layer directly underneath "parent" with the specified
    machine code as the custom property. No string matching with group
    label is performed.

    When add_missing is True, the group will be created if it can't be found.
    """

    for child_layer in parent.children():
        custom_property = child_layer.customProperty(QRIS_MAP_LAYER_MACHINE_CODE)
        if isinstance(custom_property, str) and machine_code == custom_property:
            return child_layer

    if add_missing:
        group_layer = parent.addGroup(group_label)
        group_layer.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, machine_code)
        return group_layer

    return None


def get_project_group(project: Project, add_missing=True) -> QgsLayerTreeGroup:

    root = QgsProject.instance().layerTreeRoot()
    project_group_layer = get_db_item_layer(project, root)

    if project_group_layer is None and add_missing is True:
        project_group_layer = root.addGroup(project.name)
        project_group_layer.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, project)

    return project_group_layer


def add_root_map_item(project: Project, db_item: DBItem) -> QgsLayerTreeNode:

    # First check if the item exists already within the project
    project_group = get_project_group(project)
    result = get_db_item_layer(db_item, project_group)
    if result is not None:
        return result

    # Do layer specific construction here
    if isinstance(db_item, Mask):
        machine_code = MASK_MACHINE_CODE
        group_name = 'Masks'
        map_layer = build_mask_layer(project, db_item)
    elif isinstance(db_item, Basemap):
        machine_code = BASEMAP_MACHINE_CODE
        group_name = 'Basemaps'
        map_layer = build_basemap_layer(project, db_item)

    # Finally add the new layer here
    group_layer = get_group_layer(machine_code, group_name, project_group, True)
    tree_layer_node = group_layer.addLayer(map_layer)
    tree_layer_node.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, db_item)
    return tree_layer_node


def remove_empty_groups(group_node: QgsLayerTreeGroup) -> None:

    parent_node = group_node.parent()
    if parent_node is None:
        return

    if len(group_node.children()) <= 1:
        parent_node.removeChildNode(group_node)

    if isinstance(parent_node, QgsLayerTreeGroup):
        remove_empty_groups(parent_node)


def remove_db_item_layer(project: Project, db_item: DBItem) -> None:

    project_group = get_project_group(project, False)
    if project_group is not None:
        tree_layer_node = get_db_item_layer(db_item, project_group)
        if tree_layer_node is not None:
            # QgsProject.removeMapLayer()
            parent_node = tree_layer_node.parent()
            parent_node.removeChildNode(tree_layer_node)

            remove_empty_groups(parent_node)

#             QgsMapLayerRegistry.instance().removeMapLayer(item_layer)


def build_mask_layer(project: Project, mask: Mask) -> QgsMapLayer:

    # Create a layer from the table
    mask_feature_path = project.project_file + '|layername=' + 'mask_features'
    mask_feature_layer = QgsVectorLayer(mask_feature_path, mask.name, 'ogr')
    QgsProject.instance().addMapLayer(mask_feature_layer, False)

    # hit it with qml
    qml = os.path.join(symbology_path, 'symbology', 'masks.qml')
    mask_feature_layer.loadNamedStyle(qml)
    # set the substring
    mask_feature_layer.setSubsetString('mask_id = ' + str(mask.id))
    # Set a parent assessment variable
    QgsExpressionContextUtils.setLayerVariable(mask_feature_layer, 'mask_id', mask.id)
    # Set the default value from the variable
    mask_field_index = mask_feature_layer.fields().indexFromName('mask_id')
    mask_feature_layer.setDefaultValueDefinition(mask_field_index, QgsDefaultValue("@mask_id"))

    # setup fields
    set_hidden(mask_feature_layer, 'fid', 'Mask Feature ID')
    set_hidden(mask_feature_layer, 'mask_id', 'Mask ID')
    set_alias(mask_feature_layer, 'position', 'Position')
    set_multiline(mask_feature_layer, 'description', 'Description')
    set_hidden(mask_feature_layer, 'metadata', 'Metadata')
    set_virtual_dimension(mask_feature_layer, 'area')

    return mask_feature_layer


def build_basemap_layer(project: Project, basemap: Basemap) -> QgsMapLayer:
    raster_path = os.path.join(os.path.dirname(project.project_file), basemap.path)
    raster_layer = QgsRasterLayer(raster_path, basemap.name)
    QgsProject.instance().addMapLayer(raster_layer, False)
    # TODO: raster symbology?
    return raster_layer


def map_item_receiver(qris_project: Project, item: DBItem) -> None:
    """Recieves a qris tree item model and sends to the type specific add to map function"""
    if isinstance(item, Mask):
        add_mask_to_map(qris_project, item)
    elif isinstance(item, Basemap):
        add_basemap_to_map(qris_project, item)
    elif isinstance(item, Assessment):
        add_assessment_to_map(qris_project, item)
    else:
        pass
        # TODO scratch space add to map
        # TODO raise Exception


def add_basemap_to_map(qris_project: Project, basemap: Basemap) -> None:
    basemap_id = basemap.id
    basemap_name = basemap.name
    raster_path = os.path.join(os.path.dirname(project.project_file), basemap.path)
    raster_layer = QgsRasterLayer(raster_path, basemap.name)
    QgsProject.instance().addMapLayer(raster_layer, False)
    # TODO: raster symbology?
    return raster_layer


def add_mask_to_map(qris_project: Project, item: DBItem) -> None:
    mask_id = item.id
    mask_name = item.name
    project_name = qris_project.name
    # First, check if the layer is there
    # TODO Be sure you're checking the right shit by adding properties
    if not len(QgsProject.instance().mapLayersByName(mask_name)) == 0:
        QMessageBox.information(None, 'Add Mask Layer', 'The layer is already on the map')
    else:
        # Create a layer from the table
        mask_feature_path = qris_project.project_file + '|layername=' + 'mask_features'
        mask_feature_layer = QgsVectorLayer(mask_feature_path, mask_name, 'ogr')
        QgsProject.instance().addMapLayer(mask_feature_layer, False)
        # hit it with qml
        qml = os.path.join(symbology_path, 'symbology', 'masks.qml')
        mask_feature_layer.loadNamedStyle(qml)
        # set the substring
        mask_feature_layer.setSubsetString('mask_id = ' + str(mask_id))
        # Set a parent assessment variable
        QgsExpressionContextUtils.setLayerVariable(mask_feature_layer, 'mask_id', mask_id)
        # Set the default value from the variable
        mask_field_index = mask_feature_layer.fields().indexFromName('mask_id')
        mask_feature_layer.setDefaultValueDefinition(mask_field_index, QgsDefaultValue("@mask_id"))
        # setup fields
        set_hidden(mask_feature_layer, 'fid', 'Mask Feature ID')
        set_hidden(mask_feature_layer, 'mask_id', 'Mask ID')
        set_alias(mask_feature_layer, 'position', 'Position')
        set_multiline(mask_feature_layer, 'description', 'Description')
        set_hidden(mask_feature_layer, 'metadata', 'Metadata')
        set_virtual_dimension(mask_feature_layer, 'area')
        # Get the target group and add it to the map
        group_lineage = [project_name, MASK_MACHINE_CODE]
        mask_group = set_target_layer_group(group_lineage)
        mask_group.addLayer(mask_feature_layer)


def add_assessment_to_map(qris_project, item: DBItem) -> None:
    """Starts with an assessment and then adds all of the filtered layers for that assessment and method"""
    assessment_id = item.id
    assessment_name = item.name
    assessment_methods = item.methods
    project_name = qris_project.name

    # First, check if the assessments table has been added as hidden in the project, if not add it
    # TODO add a property to this so to ensure that it is from the project database
    if len(QgsProject.instance().mapLayersByName('assessments')) == 0:
        assessments_path = qris_project.project_file + '|layername=' + 'assessments'
        assessments_layer = QgsVectorLayer(assessments_path, 'assessments', 'ogr')
        QgsProject.instance().addMapLayer(assessments_layer, False)

    # Queries the method_layers table and gets a list of layers required for that method
    for method in assessment_methods:
        conn = sqlite3.connect(qris_project.project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute("""SELECT methods.fid AS method_id,
                        layers.fid AS layer_id,
                        layers.fc_name, layers.display_name, layers.geom_type, layers.is_lookup, layers.qml
                        FROM methods
                        INNER JOIN (layers
                        INNER JOIN method_layers ON layers.fid = method_layers.layer_id)
                        ON methods.fid = method_layers.method_id
                        WHERE (((methods.fid)=?));""", [method.id])
        method_layers = curs.fetchall()
        conn.commit()
        conn.close()

        # Create the layer group list and set the target assessment group
        assessment_group_name = str(assessment_id) + '-' + assessment_name
        group_lineage = [qris_project.name, ASSESSMENT_MACHINE_CODE, assessment_group_name]
        assessment_group = set_target_layer_group(group_lineage)

        # now loop through each layer and see if they need to be added
        spatial_layers = []
        for layer in method_layers:
            # set the layer path
            layer['path'] = qris_project.project_file + '|layername=' + layer['fc_name']
            layer['ass_name'] = str(assessment_id) + '-' + layer['display_name']
            # check if it's a lookup layer, if it is send it on
            if layer['is_lookup']:
                add_lookup_table(layer)
            else:
                # add layer to spatial layers list, ensures that all lookups are added to the project first
                spatial_layers.append(layer)

        # now deal with the spatial layers
        for layer in spatial_layers:
            # check if the layer has already been added, probably better way to do this
            if len(QgsProject.instance().mapLayersByName(layer['ass_name'])) == 0:
                # if not make a layer out of it
                map_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
                QgsProject.instance().addMapLayer(map_layer, False)
                map_layer.setName(layer['ass_name'])
                # Set the QML symbology
                qml = os.path.join(symbology_path, 'symbology', layer['qml'])
                map_layer.loadNamedStyle(qml)
                # Set the assessment definition query
                map_layer.setSubsetString('assessment_id = ' + str(assessment_id))
                # Set a parent assessment variable
                QgsExpressionContextUtils.setLayerVariable(map_layer, 'assessment_id', assessment_id)
                # Set the default value from the variable
                assessment_field_index = map_layer.fields().indexFromName('assessment_id')
                map_layer.setDefaultValueDefinition(assessment_field_index, QgsDefaultValue("@assessment_id"))
                # finally add the layer to the group
                assessment_group.addLayer(map_layer)
                # send to layer specific add to map functions
                fc_name = layer['fc_name']
                if fc_name == 'dam_crests':
                    add_dam_crests(map_layer)
                elif fc_name == 'thalwegs':
                    add_thalwegs(map_layer)
                elif fc_name == 'inundation_extents':
                    add_inundation_extents(map_layer)
                elif fc_name == 'dams':
                    add_dams(map_layer)
                elif fc_name == 'jams':
                    add_jams(map_layer)
                elif fc_name == 'channel_unit_points':
                    add_channel_unit_points(map_layer)
                elif fc_name == 'channel_unit_polygons':
                    add_channel_unit_polygons(map_layer)
                else:
                    pass


# ---------- GROUP STUFF -----------
def set_target_layer_group(group_list: list) -> QgsLayerTreeGroup:
    """
    Looks for each item in the group_list recursively adding missing children as needed.
    group_list should consist of needed strings for text matching at each level of the tree heierarchy.
    returns the target group at which layers should be added.
    """
    # get the layer tree root and set to group to start
    # TODO: consider adding cusome properties to groups using for identification in the tree.
    group = QgsProject.instance().layerTreeRoot()
    # set the list of group names to search
    for group_name in group_list:
        if not any([child.name() == group_name for child in group.children()]):
            # if it ain't there add it is a new group and set to group for recursion
            new_group = group.addGroup(group_name)
            group = new_group
        else:
            # if it is there set it as the next group to search
            group = next(child for child in group.children() if child.name() == group_name)
    return group


# -------- LAYER SPECIFIC ADD TO MAP FUNCTIONS ---------
def add_lookup_table(layer: dict) -> None:
    """Checks if a lookup table has been added as private in the current QGIS session"""
    # Check if the lookup table has been added
    # TODO make sure the lookup tables are actually from the correct project geopackage
    # TODO Use custom properties to double check that the correct layers are being used
    if len(QgsProject.instance().mapLayersByName(layer['fc_name'])) == 0:
        lookup_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
        # TODO consider adding and then marking as private instead of using the False flag
        QgsProject.instance().addMapLayer(lookup_layer, False)


def add_dam_crests(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Dam Crests ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'height', 'Dam Height')
    set_virtual_dimension(map_layer, 'length')


def add_dams(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Dam ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'length', 'Dam Length')
    set_alias(map_layer, 'height', 'Dam Height')


def add_jams(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Jam ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'wood_count', 'Wood Count')
    set_alias(map_layer, 'length', 'Jam Length')
    set_alias(map_layer, 'width', 'Jam Width')
    set_alias(map_layer, 'height', 'Jam Height')


def add_inundation_extents(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Extent ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'type_id', 'lkp_inundation_extent_types', 'Extent Type')
    set_virtual_dimension(map_layer, 'area')


def add_thalwegs(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Thalweg ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'type_id', 'lkp_thalweg_types', 'Thalweg Type')
    set_virtual_dimension(map_layer, 'length')


def add_channel_unit_points(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Channel Unit ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'unit_type_id', 'lkp_channel_unit_types', 'Unit Type')
    set_value_relation(map_layer, 'structure_forced_id', 'lkp_structure_forced', 'Structure Forced')
    set_value_relation(map_layer, 'primary_channel_id', 'lkp_primary_channel', 'Primary Channel')
    set_value_relation(map_layer, 'primary_unit_id', 'lkp_primary_unit', 'Primary Unit')
    set_multiline(map_layer, 'description', 'Description')
    set_alias(map_layer, 'length', 'Length')
    set_alias(map_layer, 'width', 'Width')
    set_alias(map_layer, 'depth', 'Depth')
    set_alias(map_layer, 'percent_wetted', 'Percent Wetted')


def add_channel_unit_polygons(map_layer: QgsVectorLayer) -> None:
    set_hidden(map_layer, 'fid', 'Channel Unit ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'unit_type_id', 'lkp_channel_unit_types', 'Unit Type')
    set_value_relation(map_layer, 'structure_forced_id', 'lkp_structure_forced', 'Structure Forced')
    set_value_relation(map_layer, 'primary_channel_id', 'lkp_primary_channel', 'Primary Channel')
    set_value_relation(map_layer, 'primary_unit_id', 'lkp_primary_unit', 'Primary Unit')
    set_multiline(map_layer, 'description', 'Description')
    set_alias(map_layer, 'percent_wetted', 'Percent Wetted')


# ------ SETTING FIELD AND FORM PROPERTIES -------
def set_value_relation(map_layer: QgsVectorLayer, field_name: str, lookup_table_name: str, field_alias: str, reuse_last: bool = True) -> None:
    """Adds a Value Relation widget to the QGIS entry form. Note that at this time it assumes a Key of fid and value of name"""
    # value relation widget configuration. Just add the Layer name
    lookup_config = {
        'AllowMulti': False,
        'AllowNull': False,
        'Key': 'fid',
        'Layer': '',
        'NofColumns': 1,
        'OrderByValue': False,
        'UseCompleter': False,
        'Value': 'name'
    }
    lookup_layer_id = QgsProject.instance().mapLayersByName(lookup_table_name)[0].id()
    lookup_config['Layer'] = lookup_layer_id
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('ValueRelation', lookup_config)
    map_layer.setEditorWidgetSetup(field_index, widget_setup)
    map_layer.setFieldAlias(field_index, field_alias)
    form_config = map_layer.editFormConfig()
    form_config.setReuseLastValue(field_index, reuse_last)
    map_layer.setEditFormConfig(form_config)


def set_multiline(map_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True, 'UseHtml': False})
    map_layer.setEditorWidgetSetup(field_index, widget_setup)
    map_layer.setFieldAlias(field_index, field_alias)


def set_hidden(map_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    """Sets a field to hidden, read only, and also sets an alias just in case. Often used on fid, project_id, and assessment_id"""
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    form_config = map_layer.editFormConfig()
    form_config.setReadOnly(field_index, True)
    map_layer.setEditFormConfig(form_config)
    map_layer.setFieldAlias(field_index, field_alias)
    widget_setup = QgsEditorWidgetSetup('Hidden', {})
    map_layer.setEditorWidgetSetup(field_index, widget_setup)


def set_alias(map_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    """Just provides an alias to the field for display"""
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    map_layer.setFieldAlias(field_index, field_alias)


# ----- CREATING VIRTUAL FIELDS --------
def set_virtual_dimension(map_layer: QgsVectorLayer, dimension: str) -> None:
    """dimension should be 'area' or 'length'
    sets a virtual length field named vrt_length
    aliases the field as Length
    sets the widget type to text
    sets default value to the length expression"""
    field_name = 'vrt_' + dimension
    field_alias = dimension.capitalize()
    field_expression = 'round(${}, 0)'.format(dimension)
    virtual_field = QgsField(field_name, QVariant.Int)
    map_layer.addExpressionField(field_expression, virtual_field)
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    map_layer.setFieldAlias(field_index, field_alias)
    map_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(field_expression))
    widget_setup = QgsEditorWidgetSetup('TextEdit', {})
    map_layer.setEditorWidgetSetup(field_index, widget_setup)
