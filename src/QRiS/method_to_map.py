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


def add_assessment_method_to_map(qris_project, assessment_method_id: int):
    # """Starts with an assessment_method_id and then adds all of the filtered layers for that assessment and method"""
    # geopackage_path = os.path.join(qris_project.project_path, 'qris_project.gpkg')
    # conn = sqlite3.connect(geopackage_path)
    # curs = conn.cursor()
    # qry_string = """"""
    # curs.executescript(qry_string)
    # # design schema
    # curs.executescript(qry_string)
    # conn.commit()
    # conn.close()

    # 1. Queries the assessment layer and gets the assessment attribute values
    # a. Check if the specific Assessment Group is already added to the Project group
    # b. If not, add the group by date (or something) to an Assessment Group

    # 2. Queries the method_layers table and gets a list of layers required for that method
    # a. Loop through layer display_names field and check if they currently exist in the assessment group
    # b. If not send to layer specific add to map functions (lookup tables use general add_lookup_to_instance function)

    # 3. Layer specific add to map function
    # a. Add to the map as a layer
    # b. Hit it with .qml using path from the qml field
    # c. Set filter substring with assessment_id
    # d. Hit it with additional form and symbology configuration python
    pass


def add_lookup_table_to_map(layer_id: int):
    """Checks if a lookup table has been added as private in the current QGIS session"""
    # 1. Check if the lookup table has been added
    # 2. if not add it and set it to private
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
