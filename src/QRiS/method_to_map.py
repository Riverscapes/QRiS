import os
import sqlite3

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
    geopackage_path = os.path.join(qris_project.project_path, 'qris_project.gpkg')
    conn = sqlite3.connect(geopackage_path)
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
    for layer in method_layers:
        assessment_layer_name = str(layer['assessment_id']) + '-' + layer['display_name']
        # check if it's a lookup layer
        # if layer['is_lookup']:
        #     add_lookup_table_to_map(layer)
        # check if the layer has already been added.
        # this will need some way of differentiating by assessment and potentially only looking in the assessment group

        if len(QgsProject.instance().mapLayersByName(assessment_layer_name)) == 0:
            # if not make a layer out of it
            layer_path = geopackage_path + '|layername=' + layer['fc_name']
            # TODO probably want to give this a name that includes the assessment_id or identifier

            map_layer = QgsVectorLayer(layer_path, layer['fc_name'], 'ogr')
            QgsProject.instance().addMapLayer(map_layer, True)
            map_layer.setName(assessment_layer_name)
            # SET THE QML symbology
            # qml = os.path.join(symbology_path, 'symbology', 'project_extent.qml')
            # layer.loadNamedStyle(extent_qml)

            # SET THE ASSESSMENT ID
            map_layer.setSubsetString('assessment_id = ' + str(layer['assessment_id']))

            # SET A PARENT ASSESSMENT VARIABLE
            QgsExpressionContextUtils.setLayerVariable(map_layer, 'assessment_id', layer['assessment_id'])

            # send to layer specific add to map functions (lookup tables use general add_lookup_to_instance function)
            # first check if it's a lookup

            fc_name = layer['fc_name']
            if fc_name == 'dam_crests':
                pass
            elif fc_name == 'thalwegs':
                pass
            elif fc_name == 'inundation_extents':
                pass

            # 3. Layer specific add to map function
            # a. Add to the map as a layer
            # b. Hit it with .qml using path from the qml field
            # c. Set filter substring with assessment_id
            # d. Hit it with additional form and symbology configuration python
            # pass


def add_lookup_table_to_map(layer: tuple):
    """Checks if a lookup table has been added as private in the current QGIS session"""
    # 1. Check if the lookup table has been added
    # 2. if not add it and set it to private
    pass


# LAYER SPECIFIC ADD TO MAP FUNCTIONS
def add_dam_crests(layer: tuple):
    pass


def add_inundation_extents(layer: tuple):
    pass


def add_thalwegs(layer: tuple):
    pass


# Form configuration stuff will come back to this once we are adding to the map
# child_fields = child_layer.fields()
# field_index = child_fields.indexFromName('fid')
# child_layer.setFieldAlias(field_index, 'Child ID')

# # start the form configuration
# form_config = child_layer.editFormConfig()

# # setting read - only
# form_config.setReadOnly(field_index, True)

# # view the editor widget setup
# field = child_layer.fields()[1]
# field.editorWidgetSetup().config()


# # commit the form configuration
# child_layer.setEditFormConfig(form_config)


# # full setup for value relation
# full_config = {
#     'AllowMulti': False,
#     'AllowNull': False,
#     'Description': '',
#     'FilterExpression': '',
#     'Key': 'fid',
#     'Layer': 'parent_layer_0725a727_c80b_4a60_b87a_cef2fbf0a3df',
#     'LayerName': 'parent_layer',
#     'LayerProviderName': 'ogr',
#     'LayerSource': '/Users/nick/Desktop/Practices/project.gpkg|layername=parent_layer',
#     'NofColumns': 1,
#     'OrderByValue': False,
#     'UseCompleter': False,
#     'Value': 'name'
# }


# # reduced widget configuration
# relation_config = {
#     'AllowMulti': False,
#     'AllowNull': False,
#     'Key': 'fid',
#     'Layer': '',
#     'NofColumns': 1,
#     'OrderByValue': False,
#     'UseCompleter': False,
#     'Value': 'name'
# }

# # get the layer id
# lookup_layer = QgsProject.instance().mapLayersByName('parent_layer')[0]
# relation_config['Layer'] = lookup_layer.id()

# # apply the widget configuration
# widget_setup = QgsEditorWidgetSetup('ValueRelation', relation_config)
# field_index = child_fields.indexFromName('parent_id')
# child_layer.setEditorWidgetSetup(field_index, widget_setup)


# # setting a default value
# child_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("@parent_fid"))
