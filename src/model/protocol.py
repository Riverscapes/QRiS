import json
import sqlite3

from .db_item import DBItem
from .metric import Metric, insert_metric

from ..QRiS.protocol_parser import ProtocolDefinition, MetricDefinition

class Protocol(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, has_custom_ui: bool, description: str, version: str, metadata: dict = None, protocol_layers: dict = None):
        super().__init__('protocols', id, name, metadata)

        self.description = description
        self.machine_code = machine_code
        self.version = version
        self.has_custom_ui = has_custom_ui
        self.icon = 'protocol'
        self.protocol_layers = protocol_layers if protocol_layers else {}
        # self.metadata = metadata.get('metadata', None) if metadata else None
        # self.system_metadata: dict = metadata.get('system', None) if metadata else None
        stored_protocol_type: str = self.system_metadata.get('protocol_type', 'dce') if self.system_metadata else 'dce'
        
        if self.machine_code == 'ASBUILT':
            self.protocol_type = 'asbuilt'
        elif self.machine_code == 'DESIGN':
            self.protocol_type = 'design'
        else:
            self.protocol_type = stored_protocol_type 

    @property
    def status(self):
        if self.system_metadata:
            return self.system_metadata.get('status', 'active')
        return 'active'

    def unique_key(self):
        return f'{self.machine_code}::{self.version}'

def update_protocol(project_file: str, protocol_id: int, protocol_definition: ProtocolDefinition) -> dict:
    
    system_metadata = {
        'status': protocol_definition.status,
        'url': protocol_definition.url,
        'citation': protocol_definition.citation,
        'author': protocol_definition.author,
        'creation_date': protocol_definition.creation_date,
        'updated_date': protocol_definition.updated_date,
        'protocol_type': protocol_definition.protocol_type,
    }
    system_metadata = {k: v for k, v in system_metadata.items() if v is not None}
    out_metadata = {'system': system_metadata}
    if len(protocol_definition.metadata) > 0:
        out_metadata['metadata'] = [{'key': meta.key, 'value': meta.value, 'type': meta.type} for meta in protocol_definition.metadata]

    with sqlite3.connect(project_file) as conn:
        curs = conn.cursor()
        curs.execute('UPDATE protocols SET name = ?, description = ?, version = ?, metadata = ? WHERE id = ?',
                     (protocol_definition.label, protocol_definition.description, protocol_definition.version, json.dumps(out_metadata), protocol_id))

    return out_metadata

def insert_protocol(project_file: str, protocol_definition: ProtocolDefinition) -> Protocol:

    if protocol_definition.machine_code == 'ASBUILT':
        protocol_definition.protocol_type = 'asbuilt'
        has_custom_ui = True
    elif protocol_definition.machine_code == 'DESIGN':
        protocol_definition.protocol_type = 'design'
        has_custom_ui = True
    else:
        has_custom_ui = False

    system_metadata = {
        'status': protocol_definition.status,
        'url': protocol_definition.url,
        'citation': protocol_definition.citation,
        'author': protocol_definition.author,
        'creation_date': protocol_definition.creation_date,
        'updated_date': protocol_definition.updated_date,
        'protocol_type': protocol_definition.protocol_type,
    }
    system_metadata = {k: v for k, v in system_metadata.items() if v is not None}
    out_metadata = {'system': system_metadata}
    if len(protocol_definition.metadata) > 0:
        out_metadata['metadata'] = [{'key': meta.key, 'value': meta.value, 'type': meta.type} for meta in protocol_definition.metadata]

    with sqlite3.connect(project_file) as conn:
        curs = conn.cursor()
        curs.execute('INSERT INTO protocols (name, machine_code, has_custom_ui, description, version, metadata) VALUES (?, ?, ?, ?, ?, ?)',
                     (protocol_definition.label, protocol_definition.machine_code, has_custom_ui, protocol_definition.description, protocol_definition.version, json.dumps(out_metadata)))
        protocol_id = curs.lastrowid

    protocol = Protocol(
        protocol_id,
        protocol_definition.label,
        protocol_definition.machine_code,
        has_custom_ui,
        protocol_definition.description,
        protocol_definition.version,
        out_metadata
    )

    metrics = {}
    for metric_definition in protocol_definition.metrics:
        metric_definition: MetricDefinition
        
        metric_metadata = {}
        if metric_definition.minimum_value is not None:
            metric_metadata['minimum_value'] = metric_definition.minimum_value
        if metric_definition.maximum_value is not None:
            metric_metadata['maximum_value'] = metric_definition.maximum_value
        if metric_definition.precision is not None:
            metric_metadata['precision'] = metric_definition.precision
        if metric_definition.status is not None:
            metric_metadata['status'] = metric_definition.status
        if metric_definition.hierarchy is not None:
            metric_metadata['hierarchy'] = metric_definition.hierarchy
        
        metric_id, metric = insert_metric(
            project_file,
            metric_definition.label,
            metric_definition.id,
            protocol_definition.machine_code,
            metric_definition.description,
            metric_definition.default_level,
            metric_definition.calculation_machine_code,
            metric_definition.parameters,
            None,
            metric_definition.definition_url,
            metric_metadata,
            metric_definition.version)
        metrics[metric_id] = metric

    return protocol, metrics

def load(curs: sqlite3.Cursor, layers: list) -> dict:

    curs.execute('SELECT * FROM protocols')
    protocols = {row['id']: Protocol(
        row['id'],
        row['name'],
        row['machine_code'],
        row['has_custom_ui'],
        row['description'],
        row['version'],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}

    for protocol_id, protocol in protocols.items():
        curs.execute('SELECT layer_id FROM protocol_layers WHERE protocol_id = ?', (protocol_id,))
        protocol_layers = {row['layer_id']: layers[row['layer_id']] for row in curs.fetchall()}
        protocol.protocol_layers = protocol_layers
        protocols[protocol_id] = protocol

    return protocols
