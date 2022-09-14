import os
import sqlite3

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
    QgsExpressionContextUtils,
    QgsFieldConstraints,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsRasterBandStats
)

from qgis.PyQt.QtGui import QStandardItem, QColor
from qgis.PyQt.QtCore import Qt, QVariant

from ..model.pour_point import PourPoint
from ..model.pour_point import CONTEXT_NODE_TAG

from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.mask import MASK_MACHINE_CODE, Mask
from ..model.basemap import BASEMAP_MACHINE_CODE, Raster, RASTER_SLIDER_MACHINE_CODE
from ..model.db_item import DBItem
from ..model.mask import Mask
from ..model.project import Project, PROJECT_MACHINE_CODE
from ..model.protocol import Protocol
from ..model.layer import Layer
from ..model.event_layer import EventLayer

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

    # Handles a completely empty map
    if layer is None:
        return None

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

        # Find the basemaps group layer. If it is already in the map then
        # insert the new group layer ABOVE it rather than just add it (which
        # will cause it to get added below the basemaps).
        basemap_group_index = get_group_layer(BASEMAP_MACHINE_CODE, 'Basemaps', parent, False)

        if basemap_group_index is None:
            # No basemaps under this parent. Add the new group. It will get added last.
            group_layer = parent.addGroup(group_label)
        else:
            # Basemap group node exists. Add the new group as penultimate group.
            group_layer = parent.insertGroup(len(parent.children()) - 1, group_label)

        group_layer.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, machine_code)
        return group_layer

    return None


def get_project_group(project: Project, add_missing=True) -> QgsLayerTreeGroup:

    root = QgsProject.instance().layerTreeRoot()
    project_group_layer = get_db_item_layer(project, root)

    if project_group_layer is None and add_missing is True:
        project_group_layer = root.insertGroup(0, project.name)
        project_group_layer.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, project)

    return project_group_layer


# def add_root_map_item(project: Project, db_item: DBItem) -> QgsLayerTreeNode:

#     # First check if the item exists already within the project
#     project_group = get_project_group(project)
#     result = get_db_item_layer(db_item, project_group)
#     if result is not None:
#         return result

#     # Do layer specific construction here
#     if isinstance(db_item, Mask):
#         # machine_code = MASK_MACHINE_CODE
#         # group_name = 'Masks'
#         build_mask_layer(project, db_item)
#     elif isinstance(db_item, Basemap):
#         # machine_code = BASEMAP_MACHINE_CODE
#         # group_name = 'Basemaps'
#         build_basemap_layer(project, db_item)
#     if isinstance(db_item, Event):
#         # machine_code = EVENT_MACHINE_CODE
#         # group_name = 'Data Capture Events'
#         build_event_layer(project, db_item)
#     if isinstance(db_item, EventLayer):
#         # machine_code = EVENT_MACHINE_CODE
#         # group_name = 'Data Capture Events'
#         build_event_layer(project, db_item)


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


# def build_event_layer(project: Project, event: Event) -> None:
#     """
#     Add all layers for the event, across all protocols
#     """

#     [build_event_protocol_single_layer(project, event_layer) for event_layer in event.event_layers]


# def build_event_protocol_layer(event_layer: QgsLayerTreeGroup, project: Project, event: Event, protocol: Protocol) -> None:
#     """
#     Add all yaers in the event that are also in the protocol
#     """

#     for event_layer in event.event_layers:
#         if event_layer.layer in protocol.layers:
#             build_event_protocol_single_layer(project, event_layer)


def build_event_protocol_single_layer(project: Project, event_layer: EventLayer) -> None:
    """
    Add a single layer for an event
    """
    # if lookup table then forget about it
    if event_layer.layer.is_lookup:
        return

    # The ID of the event layer is actually the event ID!
    event = project.events[event_layer.id]

    project_group = get_project_group(project)
    # handle the DCE group
    events_group_group_layer = get_group_layer(EVENT_MACHINE_CODE + 'S', 'Data Capture Events', project_group, True)
    # handle the individual DCE group
    event_group_layer = get_group_layer(EVENT_MACHINE_CODE + str(event.id), event.name, events_group_group_layer, True)

    event_protocol_layer = get_db_item_layer(event_layer, event_group_layer)
    if event_protocol_layer is not None:
        return

    # Create a layer from the table
    fc_path = project.project_file + '|layername=' + event_layer.layer.name
    feature_layer = QgsVectorLayer(fc_path, event_layer.layer.display_name, 'ogr')
    QgsProject.instance().addMapLayer(feature_layer, False)

    # hit it with qml
    qml = os.path.join(symbology_path, 'symbology', event_layer.layer.qml)
    feature_layer.loadNamedStyle(qml)
    # set the substring
    feature_layer.setSubsetString('event_id = ' + str(event.id))
    # Set a parent assessment variable
    QgsExpressionContextUtils.setLayerVariable(feature_layer, 'event_id', event.id)
    # Set the default value from the variable
    field_index = feature_layer.fields().indexFromName('event_id')
    feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("@event_id"))

    tree_layer_node = event_group_layer.addLayer(feature_layer)
    tree_layer_node.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, event_layer)
    # send to layer specific field handlers
    layer_name = event_layer.layer.name
    if layer_name == 'dam_crests':
        configure_dam_crests(project, feature_layer)
    elif layer_name == 'thalwegs':
        configure_thalwegs(project, feature_layer)
    elif layer_name == 'inundation_extents':
        configure_inundation_extents(project, feature_layer)
    elif layer_name == 'dams':
        configure_dams(project, feature_layer)
    elif layer_name == 'jams':
        configure_jams(project, feature_layer)
    elif layer_name == 'channel_unit_points':
        configure_channel_unit_points(project, feature_layer)
    elif layer_name == 'channel_unit_polygons':
        configure_channel_unit_polygons(project, feature_layer)
    elif layer_name == 'active_extents':
        configure_active_extents(project, feature_layer)
    elif layer_name == 'zoi':
        configure_zoi(project, feature_layer)
    elif layer_name == 'structure_points':
        configure_structure_points(project, feature_layer)
    elif layer_name == 'structure_lines':
        configure_structure_lines(project, feature_layer)
    elif layer_name == 'complexes':
        configure_complexes(project, feature_layer)

    else:
        # TODO: Should probably have a notification for layers not found....
        pass


def check_for_existing_layer(project: Project, db_item: DBItem, add_missing=False):

    project_group = get_project_group(project, add_missing)
    existing_layer = get_db_item_layer(db_item, project_group)
    if existing_layer is not None:
        # Ensure it has the latest name (in case this method is called after an edit)
        existing_layer.setName(db_item.name)
        return existing_layer

    return None


def build_mask_layer(project: Project, mask: Mask) -> QgsMapLayer:

    if check_for_existing_layer(project, mask) is not None:
        return

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

    # Finally add the new layer here
    project_group = get_project_group(project, True)
    group_layer = get_group_layer(MASK_MACHINE_CODE, 'Masks', project_group, True)
    tree_layer_node = group_layer.addLayer(mask_feature_layer)
    tree_layer_node.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, mask)

    return mask_feature_layer


def build_pour_point_map_layer(project: Project, pour_point: PourPoint):

    if check_for_existing_layer(project, pour_point) is not None:
        return

    project_group = get_project_group(project)
    context_group_layer = get_group_layer(CONTEXT_NODE_TAG, 'Context', project_group, True)
    pour_point_group_layer = get_group_layer(pour_point, pour_point.name, context_group_layer, True)

    # Create a layer from the pour point
    point_feature_path = project.project_file + '|layername=' + 'pour_points'
    point_feature_layer = QgsVectorLayer(point_feature_path, 'Pour Point', 'ogr')
    point_feature_layer.setSubsetString('fid = ' + str(pour_point.id))
    QgsProject.instance().addMapLayer(point_feature_layer, False)
    pour_point_group_layer.addLayer(point_feature_layer)
    qml = os.path.join(symbology_path, 'symbology', 'pour_point.qml')
    point_feature_layer.loadNamedStyle(qml)

    catchment_feature_path = project.project_file + '|layername=' + 'catchments'
    catchment_feature_layer = QgsVectorLayer(catchment_feature_path, 'Catchment', 'ogr')
    catchment_feature_layer.setSubsetString('pour_point_id = ' + str(pour_point.id))
    QgsExpressionContextUtils.setLayerVariable(catchment_feature_layer, 'pour_point_id', pour_point.id)
    qml = os.path.join(symbology_path, 'symbology', 'catchment.qml')
    catchment_feature_layer.loadNamedStyle(qml)

    QgsProject.instance().addMapLayer(catchment_feature_layer, False)
    pour_point_group_layer.addLayer(catchment_feature_layer)

    return point_feature_layer, catchment_feature_layer


def build_basemap_layer(project: Project, basemap: Raster) -> QgsMapLayer:

    if check_for_existing_layer(project, basemap) is not None:
        return

    raster_path = os.path.join(os.path.dirname(project.project_file), basemap.path)
    raster_layer = QgsRasterLayer(raster_path, basemap.name)
    QgsProject.instance().addMapLayer(raster_layer, False)
    # TODO: raster symbology?
    # Finally add the new layer here
    project_group = get_project_group(project, True)
    group_layer = get_group_layer(BASEMAP_MACHINE_CODE, 'Basemaps', project_group, True)
    tree_layer_node = group_layer.addLayer(raster_layer)
    tree_layer_node.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, basemap)
    return raster_layer


def build_raster_slider_layer(project: Project, raster: Raster) -> QgsMapLayer:

    project_group_layer = get_project_group(project)
    raster_slider_group = get_group_layer(RASTER_SLIDER_MACHINE_CODE, 'Raster Slider', project_group_layer, True)
    raster_layer = get_db_item_layer(raster, raster_slider_group)
    if raster_layer is not None:
        return raster_layer

    # Remove any existing raster layer in this group
    raster_slider_group.removeAllChildren()

    raster_path = os.path.join(os.path.dirname(project.project_file), raster.path)
    raster_layer = QgsRasterLayer(raster_path, raster.name + ' (Raster Slider)')
    raster_slider_group.addLayer(raster_layer)
    raster_layer.setCustomProperty(QRIS_MAP_LAYER_MACHINE_CODE, raster)
    # qml = os.path.join(symbology_path, 'symbology', 'hand.qml')
    # raster_layer.loadNamedStyle(qml)
    QgsProject.instance().addMapLayer(raster_layer, False)
    return raster_layer


def get_raster_statistics(project: Project, raster: Raster):

    raster_layer = build_raster_slider_layer(project, raster)
    statistics = raster_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, raster_layer.extent(), 0)
    return statistics.minimumValue, statistics.maximumValue


def apply_raster_slider_value(project: Project, raster: Raster, raster_value: float) -> None:

    raster_layer = build_raster_slider_layer(project, raster)

    fcn = QgsColorRampShader()
    fcn.setColorRampType(QgsColorRampShader.Discrete)
    fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(raster_value, QColor(255, 20, 225), f'Threshold {raster_value}')])
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(fcn)

    renderer = QgsSingleBandPseudoColorRenderer(raster_layer.dataProvider(), 1, shader)
    raster_layer.setRenderer(renderer)
    raster_layer.triggerRepaint()


# -------- LAYER SPECIFIC ADD TO MAP FUNCTIONS ---------
def configure_dam_crests(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Dam Crests ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_map(project, feature_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_map(project, feature_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'length')


def configure_dams(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Dam ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_map(project, feature_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_map(project, feature_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(feature_layer, 'length', 'Dam Length')
    set_alias(feature_layer, 'height', 'Dam Height')


def configure_jams(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Jam ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_map(project, feature_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(feature_layer, 'wood_count', 'Wood Count')
    set_alias(feature_layer, 'length', 'Jam Length')
    set_alias(feature_layer, 'width', 'Jam Width')
    set_alias(feature_layer, 'height', 'Jam Height')
    set_multiline(feature_layer, 'description', 'Description')


def configure_inundation_extents(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Extent ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'type_id', 'lkp_inundation_extent_types', 'Extent Type')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'area')


def configure_thalwegs(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Thalweg ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'type_id', 'lkp_thalweg_types', 'Thalweg Type')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'length')


def configure_channel_unit_points(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_hidden(feature_layer, 'fid', 'Channel Unit ID')
    set_value_map(project, feature_layer, 'unit_type_id', 'lkp_channel_unit_types', 'Unit Type')
    set_value_map(project, feature_layer, 'structure_forced_id', 'lkp_structure_forced', 'Structure Forced')
    set_value_map(project, feature_layer, 'primary_channel_id', 'lkp_primary_channel', 'Primary Channel')
    set_value_map(project, feature_layer, 'primary_unit_id', 'lkp_primary_unit', 'Primary Unit')
    set_multiline(feature_layer, 'description', 'Description')
    set_alias(feature_layer, 'length', 'Length')
    set_alias(feature_layer, 'width', 'Width')
    set_alias(feature_layer, 'depth', 'Depth')
    set_alias(feature_layer, 'percent_wetted', 'Percent Wetted')
    set_multiline(feature_layer, 'description', 'Description')


def configure_channel_unit_polygons(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_hidden(feature_layer, 'fid', 'Channel Unit ID')
    set_value_map(project, feature_layer, 'unit_type_id', 'lkp_channel_unit_types', 'Unit Type')
    set_value_map(project, feature_layer, 'structure_forced_id', 'lkp_structure_forced', 'Structure Forced')
    set_value_map(project, feature_layer, 'primary_channel_id', 'lkp_primary_channel', 'Primary Channel')
    set_value_map(project, feature_layer, 'primary_unit_id', 'lkp_primary_unit', 'Primary Unit')
    set_multiline(feature_layer, 'description', 'Description')
    set_alias(feature_layer, 'percent_wetted', 'Percent Wetted')
    set_multiline(feature_layer, 'description', 'Description')


def configure_active_extents(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Extent ID')
    # We may consider adding a value map for the event ID,
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'type_id', 'lkp_active_extent_types', 'Extent Type')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'area')


def configure_zoi(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'ZOI ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'type_id', 'zoi_types', 'ZOI Type')
    set_value_map(project, feature_layer, 'stage_id', 'lkp_zoi_stage', 'ZOI Stage')
    set_multiline(feature_layer, 'description', 'Description')
    set_field_constraint_not_null(feature_layer, 'type_id', 1)
    set_field_constraint_not_null(feature_layer, 'stage_id', 1)
    set_virtual_dimension(feature_layer, 'area')
    set_created_datetime(feature_layer)


def configure_structure_points(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Structure ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'structure_type_id', 'structure_types', 'Structure Type')
    set_alias(feature_layer, 'name', 'Structure Name')
    set_multiline(feature_layer, 'description', 'Description')
    set_alias(feature_layer, 'created', 'Created')
    set_field_constraint_not_null(feature_layer, 'structure_type_id', 1)
    set_created_datetime(feature_layer)


def configure_structure_lines(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Structure ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_value_map(project, feature_layer, 'structure_type_id', 'structure_types', 'Structure Type')
    set_alias(feature_layer, 'name', 'Structure Name')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'length')
    set_alias(feature_layer, 'created', 'Created')
    set_field_constraint_not_null(feature_layer, 'structure_type_id', 1)
    set_created_datetime(feature_layer)


def configure_complexes(project: Project, feature_layer: QgsVectorLayer) -> None:
    set_hidden(feature_layer, 'fid', 'Structure ID')
    set_hidden(feature_layer, 'event_id', 'Event ID')
    set_alias(feature_layer, 'name', 'Complex Name')
    set_multiline(feature_layer, 'initial_condition', 'Initial Conditions')
    set_multiline(feature_layer, 'target_condition', 'Target Condition')
    set_multiline(feature_layer, 'description', 'Description')
    set_virtual_dimension(feature_layer, 'area')
    set_created_datetime(feature_layer)

    # ------ SETTING FIELD AND FORM PROPERTIES -------


def set_value_relation(feature_layer: QgsVectorLayer, field_name: str, lookup_table_name: str, field_alias: str, reuse_last: bool = True) -> None:
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
    # TODO this lookup needs to check custom property and should also have try except block
    lookup_config['Layer'] = feature_layer.id()
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('ValueRelation', lookup_config)
    feature_layer.setEditorWidgetSetup(field_index, widget_setup)
    feature_layer.setFieldAlias(field_index, field_alias)
    form_config = feature_layer.editFormConfig()
    form_config.setReuseLastValue(field_index, reuse_last)
    feature_layer.setEditFormConfig(form_config)


def set_value_map(project: Project, feature_layer: QgsVectorLayer, field_name: str, lookup_table_name: str, field_alias: str, desc_position: int = 1, value_position: int = 0, reuse_last: bool = True) -> None:
    """Will set a Value Map widget drop down list from the lookup database table"""
    conn = sqlite3.connect(project.project_file)
    # conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute("SELECT * FROM {};".format(lookup_table_name))
    lookup_collection = curs.fetchall()
    conn.commit()
    conn.close()
    # make a dictionary from the returned values
    lookup_list = []
    for row in lookup_collection:
        key = str(row[desc_position])
        value = row[value_position]
        lookup_list.append({key: value})
    lookup_config = {
        'map': lookup_list
    }
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('ValueMap', lookup_config)
    feature_layer.setEditorWidgetSetup(field_index, widget_setup)
    feature_layer.setFieldAlias(field_index, field_alias)
    form_config = feature_layer.editFormConfig()
    form_config.setReuseLastValue(field_index, reuse_last)
    feature_layer.setEditFormConfig(form_config)


def set_multiline(feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True, 'UseHtml': False})
    feature_layer.setEditorWidgetSetup(field_index, widget_setup)
    feature_layer.setFieldAlias(field_index, field_alias)
    form_config = feature_layer.editFormConfig()
    form_config.setLabelOnTop(field_index, True)
    feature_layer.setEditFormConfig(form_config)


def set_hidden(feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    """Sets a field to hidden, read only, and also sets an alias just in case. Often used on fid, project_id, and event_id"""
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    form_config = feature_layer.editFormConfig()
    form_config.setReadOnly(field_index, True)
    feature_layer.setEditFormConfig(form_config)
    feature_layer.setFieldAlias(field_index, field_alias)
    widget_setup = QgsEditorWidgetSetup('Hidden', {})
    feature_layer.setEditorWidgetSetup(field_index, widget_setup)


def set_alias(feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
    """Just provides an alias to the field for display"""
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    feature_layer.setFieldAlias(field_index, field_alias)


# ----- CREATING VIRTUAL FIELDS --------
def set_virtual_dimension(feature_layer: QgsVectorLayer, dimension: str) -> None:
    """dimension should be 'area' or 'length'
    sets a virtual length field named vrt_length
    aliases the field as Length (m)
    sets the widget type to text
    sets default value to the dimension expression"""
    field_name = 'vrt_' + dimension
    field_alias = dimension.capitalize() + ' (m)'
    field_expression = 'round(${}, 0)'.format(dimension)
    virtual_field = QgsField(field_name, QVariant.Int)
    feature_layer.addExpressionField(field_expression, virtual_field)
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    feature_layer.setFieldAlias(field_index, field_alias)
    feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(field_expression))
    widget_setup = QgsEditorWidgetSetup('TextEdit', {})
    feature_layer.setEditorWidgetSetup(field_index, widget_setup)


def set_created_datetime(feature_layer: QgsVectorLayer) -> None:
    """Will set a date time created field to a default value of now() and also set it to read only"""
    fields = feature_layer.fields()
    field_index = fields.indexFromName('created')
    feature_layer.setFieldAlias(field_index, 'Created')
    feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("now()"))
    form_config = feature_layer.editFormConfig()
    form_config.setReadOnly(field_index, True)
    feature_layer.setEditFormConfig(form_config)


def set_field_constraint_not_null(feature_layer: QgsVectorLayer, field_name: str, constraint_strength: int) -> None:
    """Sets a not null constraint and strength"""
    if constraint_strength == 1:
        strength = QgsFieldConstraints.ConstraintStrengthSoft
    elif constraint_strength == 2:
        strength = QgsFieldConstraints.ConstraintStrengthHard
    fields = feature_layer.fields()
    field_index = fields.indexFromName(field_name)
    feature_layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintNotNull, strength)
