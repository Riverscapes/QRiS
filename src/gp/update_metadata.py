# Check the metatdata field of the event layers and update if needed

import json
import sqlite3

from osgeo import ogr

def update_metadata(project_file: str):

    outputs = {}
    with sqlite3.connect(project_file) as conn:
        c = conn.cursor()
        # get the list of attribute fields for each layer. This is the display_label
        c.execute("SELECT id, metadata FROM Layers")
        rows = c.fetchall()
        attribute_fields = {}
        for row in rows:
            layer_id = row[0]
            if not row[1]:
                continue
            meta = json.loads(row[1])
            if not meta:
                continue
            if 'fields' not in meta:
                continue
            meta_fields = meta['fields']
            for meta_field in meta_fields:
                if layer_id not in attribute_fields:
                    attribute_fields[layer_id] = []
                attribute_fields[layer_id].append(meta_field['label'])
        
        for layer in ['dce_points', 'dce_lines', 'dce_polygons']:
            c.execute(f"SELECT fid, event_layer_id, metadata FROM {layer}")
            rows = c.fetchall()
            for row in rows:
                layer_id = row[1]
                if not row[1]:
                    continue
                meta = json.loads(row[2])
                if not meta:
                    continue
                if not (set(meta.keys()) <= {'attributes', 'metadata'}):
                    new_meta = {}
                    # restructure the metadata. if the key is in the attribute_fields, then it is an attribute, otherwise it is metadata
                    for key, value in meta.items():
                        if key in attribute_fields[layer_id]:
                            new_meta['attributes'] = new_meta.get('attributes', {})
                            new_meta['attributes'][key] = value
                        else:
                            new_meta['metadata'] = new_meta.get('metadata', {})
                            new_meta['metadata'][key] = value

                    # update the metadata
                    if layer not in outputs:
                        outputs[layer] = []
                    outputs[layer].append((row[0], json.dumps(new_meta)))
    
    # update the metadata using ogr
    for layer, rows in outputs.items():
        ds: ogr.DataSource = ogr.Open(project_file, 1)
        lyr: ogr.Layer = ds.GetLayerByName(layer)
        for row in rows:
            feat: ogr.Feature = lyr.GetFeature(row[0])
            feat.SetField('metadata', row[1])
            lyr.SetFeature(feat)
        ds = None


def check_metadata(project_file: str):

    with sqlite3.connect(project_file) as conn:
        c = conn.cursor()
        for layer in ['dce_points', 'dce_lines', 'dce_polygons']:
            c.execute(f"SELECT metadata FROM {layer}")
            rows = c.fetchall()
            for row in rows:
                value = row[0]
                if value is None:
                    continue
                meta = json.loads(value)
                # if meta is empty, continue
                if not meta:
                    continue
                # check if metadata has only attributes and or metatdata as keys
                if any([key not in ['attributes', 'metadata'] for key in meta.keys()]):
                    return False

    return True
