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
        self.hierarchy = metadata.get('hierarchy', None) if metadata else None

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

    :param project_file: The path to the project file
    :param layer_definition: The LayerDefinition object to insert
    :param protocol: The Protocol object to associate with the layer
    :return: The new Layer object and the updated Protocol object
    """

    fields = []
    for field in layer_definition.fields:
        
        out_field = {
            'id': field.id,
            'type': field.type,
            'label': field.label,
            'description': field.description,
            'values': field.values,
            'default_value': field.default_value,
        }
        if field.required is True:
            out_field['required'] = field.required

        if field.allow_custom_values is True:
            out_field['allow_custom_values'] =  field.allow_custom_values

        if field.allow_multiple_values is True:
            out_field['allow_multiple_values'] = field.allow_multiple_values

        if field.visibility_field is not None:
            visibility = {'field_id': field.visibility_field, 'values': field.visibility_values}
            out_field['visibility'] = visibility
        if field.derived_values is not None:
            out_field['derived_values'] = field.derived_values
        out_field = {k: v for k, v in out_field.items() if v is not None}
        fields.append(out_field)
        
    metadata = {}
    if layer_definition.menu_items is not None:
        metadata['menu_items'] = layer_definition.menu_items
    if layer_definition.hierarchy is not None:
        metadata['hierarchy'] = layer_definition.hierarchy
    if len(fields) > 0:
        metadata['fields'] = fields
    metadata = {k: v for k, v in metadata.items() if v is not None}

    with sqlite3.connect(project_file) as conn:
        curs = conn.cursor()
        
        # Get the maximum existing ID and increment it by one
        curs.execute('SELECT MAX(id) FROM layers')
        max_id = curs.fetchone()[0]
        new_id = (max_id + 1) if max_id is not None else 1

        curs.execute('INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, description, version, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (new_id, layer_definition.id, layer_definition.label, layer_definition.symbology, False, layer_definition.geom_type, layer_definition.description, layer_definition.version, json.dumps(metadata)))
    
        layer_id = new_id
        curs.execute('INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (?, ?)', (protocol.id, layer_id))

    layer = Layer(
        layer_id,
        layer_definition.id,
        layer_definition.label,
        layer_definition.symbology,
        False,
        layer_definition.geom_type,
        layer_definition.description,
        metadata
    )

    protocol.protocol_layers[layer_id] = layer

    return layer, protocol
    
def check_and_remove_unused_layers(qris_project):
    
    with sqlite3.connect(qris_project.project_file) as conn:
        curs = conn.cursor()
    
        # Remove any layers from the project and the db that are no longer used in any of the project events
        layers = {key: layer for key, layer in qris_project.layers.items()}
        for key, layer in layers.items():
            used = False
            for event in qris_project.events.values():
                if layer.id in [event_layer.layer.id for event_layer in event.event_layers]:
                    used = True
                    break
            if not used:
                del qris_project.layers[key]
                curs.execute('DELETE FROM layers WHERE id = ?', (layer.id,))
                curs.execute('DELETE FROM protocol_layers WHERE layer_id = ?', (layer.id,))
                curs.execute('DELETE FROM event_layers WHERE layer_id = ?', (layer.id,))
                conn.commit()

        # now clear any protocols that are no longer used
        protocols = {key: protocol for key, protocol in qris_project.protocols.items()}
        for key, protocol in protocols.items():
            protocol_layers = [layer_id for layer_id in protocol.protocol_layers.keys()]
            for layer_id in protocol_layers:
                if layer_id not in qris_project.layers.keys():
                    del protocol.protocol_layers[layer_id]
            if len(protocol.protocol_layers) == 0:  # no layers left in the protocol
                del qris_project.protocols[key]
                curs.execute('DELETE FROM metrics WHERE protocol_id = ?', (protocol.id,))
                curs.execute('DELETE FROM protocols WHERE id = ?', (protocol.id,))
                conn.commit()
                
    return qris_project