import sqlite3
import json

from qgis.core import QgsWkbTypes

from .db_item import DBItem

from ..QRiS.protocol_parser import LayerDefinition

from typing import Dict

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

    def __init__(self, id: int, layer_id: str, layer_version, display_name: str, qml: str, is_lookup: bool, geom_type: str, description: str, metadata: dict = None):
        # Must use the display name as the official db_item name so that it is the string displayed in UI
        super().__init__('layers', id, display_name, metadata)
        self.layer_id = layer_id
        self.layer_version = layer_version
        self.qml = qml
        self.is_lookup = is_lookup
        self.geom_type = geom_type
        self.description = description
        self.icon = 'layer'

    def unique_key(self):
        return f'{self.layer_id}::{self.layer_version}'
    
    def get_layer_protocol(self, protocols: dict):
        for protocol in protocols.values():
            if self.id in protocol.protocol_layers:
                return protocol
        return None
    
    def set_metadata(self, metadata: dict) -> None:
        super().set_metadata(metadata)
        self.fields = self.metadata.get('fields', None)
        self.hierarchy = self.metadata.get('hierarchy', None)


def load_layers(curs: sqlite3.Cursor) -> Dict[int, Layer]:

    curs.execute('SELECT * FROM layers')
    return {row['id']: Layer(
        row['id'],
        row['fc_name'],
        row['version'],
        row['display_name'],
        row['qml'],
        row['is_lookup'] != 0,
        row['geom_type'],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


# method to load new layers from layer definition object
def insert_layer(project_file: str, layer_definition: LayerDefinition, protocol) -> tuple:
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
            out_field['value_required'] = field.required

        if field.allow_custom_values is True:
            out_field['allow_custom_values'] =  field.allow_custom_values

        if field.allow_multiple_values is True:
            out_field['allow_multiple_values'] = field.allow_multiple_values

        if field.visibility_field is not None:
            visibility = {'field_id': field.visibility_field, 'values': field.visibility_values}
            out_field['visibility'] = visibility
        if field.derived_values is not None:
            out_field['derived_values'] = field.derived_values
        if field.slider is not None:
            out_field['slider'] = field.slider
        if field.min is not None:
            out_field['min'] = field.min
        if field.max is not None:
            out_field['max'] = field.max
        if field.precision is not None:
            out_field['precision'] = field.precision
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
        layer_definition.version,
        layer_definition.label,
        layer_definition.symbology,
        False,
        layer_definition.geom_type,
        layer_definition.description,
        metadata
    )

    protocol.protocol_layers[layer_id] = layer

    return layer, protocol
    
def update_layer(project_file: str, layer_id: int, layer_definition: LayerDefinition) -> bool:
    """Updates an existing layer definition in the database.
    Supports updating label, symbology, description, hierarchy, menu_items, and field attributes.
    """
    with sqlite3.connect(project_file) as conn:
        conn.row_factory = sqlite3.Row
        curs = conn.cursor()
        
        # Fetch current layer data and metadata
        curs.execute('SELECT display_name, qml, description, metadata FROM layers WHERE id = ?', (layer_id,))
        row = curs.fetchone()
        if not row:
            return False
            
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        existing_fields = metadata.get('fields', [])
        
        layer_updated = False
        
        # 1. Update Core Columns (display_name, qml, description)
        columns_to_update = []
        params = []
        
        if row['display_name'] != layer_definition.label:
            columns_to_update.append("display_name = ?")
            params.append(layer_definition.label)
            layer_updated = True
            
        if row['qml'] != layer_definition.symbology:
            columns_to_update.append("qml = ?")
            params.append(layer_definition.symbology)
            layer_updated = True
            
        if row['description'] != layer_definition.description:
            columns_to_update.append("description = ?")
            params.append(layer_definition.description)
            layer_updated = True

        if columns_to_update:
             sql = f"UPDATE layers SET {', '.join(columns_to_update)} WHERE id = ?"
             params.append(layer_id)
             curs.execute(sql, params)
             conn.commit()

        # 2. Update Metadata Properties (hierarchy, menu_items)
        metadata_changed = False
        
        # Hierarchy
        new_hierarchy = layer_definition.hierarchy if layer_definition.hierarchy is not None else []
        current_hierarchy = metadata.get('hierarchy', [])
        # Normalizing to None if empty list for consistent comparison if preferred, or just list
        if new_hierarchy != current_hierarchy:
             if new_hierarchy:
                 metadata['hierarchy'] = new_hierarchy
             elif 'hierarchy' in metadata: # Remove key if now empty/none
                 del metadata['hierarchy']
             metadata_changed = True

        # Menu Items
        new_menu_items = layer_definition.menu_items if layer_definition.menu_items is not None else []
        current_menu_items = metadata.get('menu_items', [])
        if new_menu_items != current_menu_items:
            if new_menu_items:
                metadata['menu_items'] = new_menu_items
            elif 'menu_items' in metadata:
                 del metadata['menu_items']
            metadata_changed = True

        # 3. Check and update fields
        if existing_fields:
            for field_def in layer_definition.fields:
                for existing_field in existing_fields:
                    if existing_field['id'] == field_def.id:
                        # Check and update value_required
                        is_required = field_def.required
                        current_required = existing_field.get('value_required', False)
                        
                        if current_required != is_required:
                            existing_field['value_required'] = is_required
                            metadata_changed = True
                        
                        # Update min/max/precision
                        for key, val in [('min', field_def.min), ('max', field_def.max), ('precision', field_def.precision)]:
                            current_val = existing_field.get(key, None)
                            if val is not None and current_val != val:
                                existing_field[key] = val
                                metadata_changed = True
                            elif val is None and key in existing_field:
                                # If value is removed in new definition, remove it from existing
                                del existing_field[key]
                                metadata_changed = True
        
        if metadata_changed:
            metadata['fields'] = existing_fields # Ensure fields are written back
            curs.execute('UPDATE layers SET metadata = ? WHERE id = ?', (json.dumps(metadata), layer_id))
            conn.commit()
            layer_updated = True
            
        return layer_updated

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
                # Collect metric_ids to delete
                metric_ids_to_delete = [metric_id for metric_id, metric in qris_project.metrics.items() if metric.protocol_machine_code == protocol.machine_code]
                for metric_id in metric_ids_to_delete:
                    del qris_project.metrics[metric_id]

                # Manually clean up analysis_metrics since ON DELETE CASCADE is missing in schema for this relationship
                curs.execute('DELETE FROM analysis_metrics WHERE metric_id IN (SELECT id FROM metrics WHERE protocol_id = ?)', (protocol.id,))
                curs.execute('DELETE FROM metrics WHERE protocol_id = ?', (protocol.id,))
                curs.execute('DELETE FROM protocols WHERE id = ?', (protocol.id,))
                conn.commit()
                # remove any metrics associated with the protocol
                

    return qris_project
