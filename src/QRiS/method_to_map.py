import os
import sqlite3

from random import randint, randrange


from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsVectorLayer,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
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

from .qt_user_role import item_code

# path to symbology directory
symbology_path = os.path.dirname(os.path.dirname(__file__))


def add_assessment_layer_to_map(assessment_id, layer_id, fc_name, display_name, qml_path):
    # Query the layers DB table to get the layer display name and QML file Path for the layer_id
    # If layer exists in map with the same assessment_id definition query then do nothing
    # Create QGISLayer for the layer feature class name
    # apply definition query with assessment_id
    # Apply symbology from QML file
    # Build layer edit form in code depending on the layer type
    pass


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def add_assessment_method_to_map(qris_project, assessment_method_id: int):
    """Starts with an assessment_method_id and then adds all of the filtered layers for that assessment and method"""
    # First, check if the assessments table has been added as hidden in the project, if not add it
    if len(QgsProject.instance().mapLayersByName('assessments')) == 0:
        assessments_path = qris_project.project_file + '|layername=' + 'assessments'
        assessments_layer = QgsVectorLayer(assessments_path, 'assessments', 'ogr')
        QgsProject.instance().addMapLayer(assessments_layer, False)

    conn = sqlite3.connect(qris_project.project_file)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    # 2. Queries the method_layers table and gets a list of layers required for that method -done
    # a. also returns the parent assessment_id
    curs.execute("""SELECT assessments.fid AS assessment_id,
                    assessment_methods.fid AS assessment_method_id,
                    methods.fid AS method_id,
                    layers.fid AS layer_id,
                    layers.fc_name,
                    layers.display_name,
                    layers.geom_type,
                    layers.is_lookup,
                    layers.qml FROM (methods
                    INNER JOIN (assessments
                    INNER JOIN assessment_methods ON assessments.fid = assessment_methods.assessment_id)
                    ON methods.fid = assessment_methods.method_id)
                    INNER JOIN (layers
                    INNER JOIN method_layers
                    ON layers.fid = method_layers.layer_id)
                    ON methods.fid = method_layers.method_id
                    WHERE (((assessment_methods.fid)=?));""", [assessment_method_id])
    method_layers = curs.fetchall()
    conn.commit()
    conn.close()

    # a. Check if the specific Assessment Group is already added to the Project group
    # b. If not, add the group by date (or something) to an Assessment Group

    # now loop through each layer and see if they need to be added
    spatial_layers = []
    for layer in method_layers:
        # set the layer path
        layer['path'] = qris_project.project_file + '|layername=' + layer['fc_name']
        layer['ass_name'] = str(layer['assessment_id']) + '-' + layer['display_name']
        # check if it's a lookup layer, if it is send it on
        if layer['is_lookup']:
            add_lookup_table_to_map(layer)
        else:
            # add layer to spatial layers list, ensures that all lookups are added to the project first
            spatial_layers.append(layer)

    # now deal with the spatial layers
    for layer in spatial_layers:
        # check if the layer has already been added.
        if len(QgsProject.instance().mapLayersByName(layer['ass_name'])) == 0:
            # if not make a layer out of it
            map_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
            QgsProject.instance().addMapLayer(map_layer, True)
            map_layer.setName(layer['ass_name'])
            # Set the QML symbology
            qml = os.path.join(symbology_path, 'symbology', layer['qml'])
            map_layer.loadNamedStyle(qml)
            # Set the assessment definition query
            map_layer.setSubsetString('assessment_id = ' + str(layer['assessment_id']))
            # Set a parent assessment variable
            QgsExpressionContextUtils.setLayerVariable(map_layer, 'assessment_id', layer['assessment_id'])
            # Set the default value from the variable
            assessment_field_index = map_layer.fields().indexFromName('assessment_id')
            map_layer.setDefaultValueDefinition(assessment_field_index, QgsDefaultValue("@assessment_id"))
            # send to layer specific add to map functions (lookup tables use general add_lookup_to_instance function)
            # first check if it's a lookup
            fc_name = layer['fc_name']
            if fc_name == 'dam_crests':
                pass
            elif fc_name == 'thalwegs':
                pass
            elif fc_name == 'inundation_extents':
                add_inundation_extents(map_layer)


def add_lookup_table_to_map(layer: dict):
    """Checks if a lookup table has been added as private in the current QGIS session"""
    # Check if the lookup table has been added
    if len(QgsProject.instance().mapLayersByName(layer['fc_name'])) == 0:
        lookup_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
        QgsProject.instance().addMapLayer(lookup_layer, False)


# LAYER SPECIFIC ADD TO MAP FUNCTIONS
def add_dam_crests(map_layer: QgsVectorLayer):
    pass


def add_inundation_extents(map_layer: QgsVectorLayer):
    configure_value_relation(map_layer, 'type_id', 'lkp_inundation_extent_types')
    configure_value_relation(map_layer, 'assessment_id', 'assessments')


def add_thalwegs(map_layer: QgsVectorLayer):
    pass


# Function for setting form widgets
def configure_value_relation(map_layer: QgsVectorLayer, field_name: str, lookup_table_name: str):
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


def set_default_value_from_variable(map_layer: QgsVectorLayer, field_name: str, variable_name):
    pass

# thalwegs = QgsProject.instance().mapLayersByName('thalwegs')[0]

# # Form configuration stuff will come back to this once we are adding to the map
# fields = thalwegs.fields()
# thalwegs.setFieldAlias(field_index, 'Thalweg ID')

# # # start the form configuration
# form_config = thalwegs.editFormConfig()

# # # setting read - only
# # form_config.setReadOnly(field_index, True)

# # # view the editor widget setup
# field = thalwegs.fields()[2]
# field.editorWidgetSetup().config()

# # # commit the form configuration
# child_layer.setEditFormConfig(form_config)

# # # full setup for value relation
# full_config = {
#     'AllowMulti': False,
#     'AllowNull': False,
#     'Description': '',
#     'FilterExpression': '',
#     'Key': 'fid',
#     'LayerName': 'lkp_thalweg_types',
#     'LayerProviderName': 'ogr',
#     'LayerSource': '/Users/nick/Desktop/asdF3/qris_project.gpkg|layername=lkp_thalweg_types',
#     'NofColumns': 1,
#     'OrderByValue': False,
#     'UseCompleter': False,
#     'Value': 'name'
# }


# # # get the layer id
# lookup_layer = QgsProject.instance().mapLayersByName('parent_layer')[0]
# relation_config['Layer'] = lookup_layer.id()

# # # apply the widget configuration
# widget_setup = QgsEditorWidgetSetup('ValueRelation', full_config)
# field_index = child_fields.indexFromName('parent_id')
# thalwegs.setEditorWidgetSetup(2, widget_setup)

# # setting a default value
# child_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("@parent_fid"))
