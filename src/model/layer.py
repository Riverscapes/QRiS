import sqlite3
import json

from qgis.core import QgsWkbTypes

from .db_item import DBItem
from .protocol import Protocol
from ..QRiS.protocol_parser import LayerDefinition


class Layer(DBItem):
    """Represents the definition of a layer that can be used by an event protocol.

    This class possesses the properties needed to add the layer to the map (with the addition of
    the event id definition query filter."""

    GEOMETRY_TYPES = {'Point': QgsWkbTypes.GeometryType.PointGeometry,
                      'Linestring': QgsWkbTypes.GeometryType.LineGeometry,
                      'Polygon': QgsWkbTypes.GeometryType.PolygonGeometry}
    
    DCE_LAYER_NAMES = {'Point': 'dce_points',
                      'Linestring': 'dce_lines',
                      'Polygon': 'dce_polygons'}

    def __init__(self, id: int, layer_id: str, display_name: str, qml: str, is_lookup: bool, geom_type: str, description: str, metadata: dict = None):
        # Must use the display name as the official db_item name so that it is the string displayed in UI
        super().__init__('layers', id, display_name)
        self.layer_id = layer_id
        self.qml = qml
        self.is_lookup = is_lookup
        self.geom_type = geom_type
        self.description = description
        self.icon = 'layer'
        self.metadata = metadata
        self.fields = metadata.get('fields', None) if metadata else None
        self.hierarchy = metadata['hierarchy'] if metadata else None

    def unique_key(self):
        return f'{self.layer_id}'

def load_layers(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM layers')
    return {row['id']: Layer(
        row['id'],
        row['fc_name'],
        row['display_name'],
        row['qml'],
        row['is_lookup'] != 0,
        row['geom_type'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


# method to load new layers from layer definition object
def insert_layer(project_file: str, layer_definition: LayerDefinition, protocol: Protocol) -> tuple:
    """Insert a new layer into the database from a LayerDefinition object.

    :param curs: The database cursor
    :param layer_definition: The LayerDefinition object to insert
    :return: The id of the new layer
    """

    fields = []
    for field in layer_definition.fields:
        fields.append({
            'id': field.id,
            'type': field.type,
            'label': field.label,
            'required': field.required,
            'custom_values_allowed': field.custom_values_allowed,
            'description': field.description,
            'values': field.values,
            'default_value': field.default_value,
            'visibility_field': field.visibility_field,
            'visibility_values': field.visibility_values
        })
        
    metadata = {'menu_items': layer_definition.menu_items, 'hierarchy': layer_definition.hierarchy, 'fields': fields}
    
    with sqlite3.connect(project_file) as conn:
        curs = conn.cursor()
        curs.execute('INSERT INTO layers (fc_name, display_name, qml, is_lookup, geom_type, description, version, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (layer_definition.id, layer_definition.label, layer_definition.symbology, False, layer_definition.geom_type, layer_definition.description, layer_definition.version, json.dumps(metadata)))
    
        layer_id = curs.lastrowid
        curs.execute('INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (?, ?)', (protocol.id, layer_id))

    layer = Layer(
        layer_id,
        layer_definition.id,
        layer_definition.label,
        layer_definition.symbology,
        False,
        layer_definition.geom_type,
        layer_definition.description,
        layer_definition.__dict__
    )

    protocol.protocol_layers[layer_id] = layer

    return layer, protocol