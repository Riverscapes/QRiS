import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

# Usage: python check_protocol_integrity.py <protocols_folder> <old_protocols_folder>
# <protocols_folder>: path to folder with new/edited protocol XMLs
# <old_protocols_folder>: path to folder with previous/approved protocol XMLs

# Helper: Parse protocol XML into a dict structure

def parse_protocol_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    protocol = {'layers': {}, 'metrics': {}, 'fields': defaultdict(dict)}
    for layer_elem in root.findall('./Layers/Layer'):
        layer_id = layer_elem.attrib['id']
        version = layer_elem.attrib.get('version', None)
        status = layer_elem.attrib.get('status', '').lower()
        protocol['layers'][(layer_id, version)] = {'elem': layer_elem, 'status': status}
        for field_elem in layer_elem.findall('./Fields/*'):
            field_id = field_elem.attrib['id']
            fver = field_elem.attrib.get('version', None)
            fstatus = field_elem.attrib.get('status', '').lower()
            protocol['fields'][(layer_id, version)][(field_id, fver)] = {'elem': field_elem, 'status': fstatus}
    for metric_elem in root.findall('./Metrics/Metric'):
        metric_id = metric_elem.attrib['id']
        mver = metric_elem.attrib.get('version', None)
        mstatus = metric_elem.attrib.get('status', '').lower()
        protocol['metrics'][(metric_id, mver)] = {'elem': metric_elem, 'status': mstatus}
    return protocol

# Helper: Compare two protocol dicts

def compare_protocols(old, new, errors):
    # Check for removed layers (not present and not deprecated)
    for layer_key, old_layer in old['layers'].items():
        if layer_key not in new['layers']:
            errors.append(f"Layer removed: {layer_key}")
        else:
            new_layer = new['layers'][layer_key]
            if old_layer['status'] != 'deprecated' and new_layer['status'] == 'deprecated':
                # Allowed: deprecation
                continue
    # Check for removed fields (not present and not deprecated)
    for layer_key, fields in old['fields'].items():
        for field_key, old_field in fields.items():
            if layer_key not in new['fields'] or field_key not in new['fields'][layer_key]:
                errors.append(f"Field removed: {field_key} from layer {layer_key}")
            else:
                new_field = new['fields'][layer_key][field_key]
                if old_field['status'] != 'deprecated' and new_field['status'] == 'deprecated':
                    continue
    # Check for removed metrics (not present and not deprecated)
    for metric_key, old_metric in old['metrics'].items():
        if metric_key not in new['metrics']:
            errors.append(f"Metric removed: {metric_key}")
        else:
            new_metric = new['metrics'][metric_key]
            if old_metric['status'] != 'deprecated' and new_metric['status'] == 'deprecated':
                continue
    # Check for new fields
    for layer_key, fields in new['fields'].items():
        for field_key in fields:
            if layer_key not in old['fields'] or field_key not in old['fields'][layer_key]:
                errors.append(f"New field added: {field_key} to layer {layer_key}")
    # Check for new attributes in fields
    for layer_key, fields in new['fields'].items():
        for field_key, field_info in fields.items():
            if layer_key in old['fields'] and field_key in old['fields'][layer_key]:
                old_elem = old['fields'][layer_key][field_key]['elem']
                field_elem = field_info['elem']
                for attr in field_elem.attrib:
                    if attr not in old_elem.attrib:
                        errors.append(f"New attribute '{attr}' added to field {field_key} in layer {layer_key}")
                for attr in old_elem.attrib:
                    if attr not in field_elem.attrib:
                        errors.append(f"Attribute '{attr}' removed from field {field_key} in layer {layer_key}")
                # Check for data type change
                if field_elem.tag != old_elem.tag:
                    errors.append(f"Data type changed for field {field_key} in layer {layer_key}: {old_elem.tag} -> {field_elem.tag}")
    # Check for metric parameter/field/visibility/value edits
    for metric_key, metric_info in new['metrics'].items():
        if metric_key in old['metrics']:
            metric_elem = metric_info['elem']
            old_metric_elem = old['metrics'][metric_key]['elem']
            # Parameters
            for param in metric_elem.findall('./Parameters/*'):
                tag = param.tag
                old_params = old_metric_elem.findall(f'./Parameters/{tag}')
                if not old_params:
                    errors.append(f"New parameter '{tag}' added to metric {metric_key}")
            for param in old_metric_elem.findall('./Parameters/*'):
                tag = param.tag
                new_params = metric_elem.findall(f'./Parameters/{tag}')
                if not new_params:
                    errors.append(f"Parameter '{tag}' removed from metric {metric_key}")
            # TODO: Forbid edits to existing parameters (deep compare)
    # TODO: Forbid edits to Visibility or Values in fields (deep compare)

# Integrity checks

def check_integrity(protocol, errors):
    # layer_id_ref in metrics must reference a layer_id
    # Only consider non-deprecated layers/fields for reference checks
    layer_ids = set(lid for (lid, ver), l in protocol['layers'].items() if l['status'] != 'deprecated')
    field_ids_by_layer = {}
    for (lid, lver), fields in protocol['fields'].items():
        if protocol['layers'][(lid, lver)]['status'] == 'deprecated':
            continue
        field_ids_by_layer[lid] = set(fid for (fid, fver), f in fields.items() if f['status'] != 'deprecated')
    for metric_info in protocol['metrics'].values():
        metric = metric_info['elem']
        for dce_layer in metric.findall('.//DCELayer'):
            layer_id_ref = dce_layer.attrib.get('layer_id_ref')
            if layer_id_ref and layer_id_ref not in layer_ids:
                errors.append(f"layer_id_ref {layer_id_ref} in metric {metric.attrib['id']} does not reference a valid layer_id")
            # field_id_ref in AttributeFilter or CountField
            for attr_filter in dce_layer.findall('.//AttributeFilter'):
                field_id_ref = attr_filter.attrib.get('field_id_ref')
                if field_id_ref and (layer_id_ref not in field_ids_by_layer or field_id_ref not in field_ids_by_layer[layer_id_ref]):
                    errors.append(f"field_id_ref {field_id_ref} in AttributeFilter of metric {metric.attrib['id']} does not reference a valid field in layer {layer_id_ref}")
            for count_field in dce_layer.findall('.//CountField'):
                field_id_ref = count_field.attrib.get('field_id_ref')
                if field_id_ref and (layer_id_ref not in field_ids_by_layer or field_id_ref not in field_ids_by_layer[layer_id_ref]):
                    errors.append(f"field_id_ref {field_id_ref} in CountField of metric {metric.attrib['id']} does not reference a valid field in layer {layer_id_ref}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python check_protocol_integrity.py <protocols_folder> <old_protocols_folder>")
        sys.exit(1)
    new_folder = sys.argv[1]
    old_folder = sys.argv[2]
    errors = []
    for fname in os.listdir(new_folder):
        if not fname.endswith('.xml'):
            continue
        new_path = os.path.join(new_folder, fname)
        old_path = os.path.join(old_folder, fname)
        if not os.path.exists(old_path):
            print(f"Skipping {fname}: no previous version found.")
            continue
        new_protocol = parse_protocol_xml(new_path)
        old_protocol = parse_protocol_xml(old_path)
        compare_protocols(old_protocol, new_protocol, errors)
        check_integrity(new_protocol, errors)
    if errors:
        print("Protocol integrity check failed:")
        for err in errors:
            print(" -", err)
        sys.exit(2)
    else:
        print("All protocol XMLs passed integrity checks.")
        sys.exit(0)
