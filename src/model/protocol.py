import json
import sqlite3

from .db_item import DBItem
from ..QRiS.protocol_parser import ProtocolDefinition

class Protocol(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, has_custom_ui: bool, description: str, version: str, metadata: dict = None, protocol_layers: dict = None):
        super().__init__('protocols', id, name)

        self.description = description
        self.machine_code = machine_code
        self.version = version
        self.has_custom_ui = has_custom_ui
        self.icon = 'protocol'
        self.protocol_layers = protocol_layers if protocol_layers else {}
        self.metadata = metadata.get('metadata', None) if metadata else None
        self.system_metadata = metadata.get('system', None) if metadata else None

    def unique_key(self):
        return f'{self.machine_code}::{self.version}'

def insert_protocol(project_file: str, protocol_definition: ProtocolDefinition) -> Protocol:

    has_custom_ui = True if protocol_definition.machine_code in ['ASBUILT', 'DESIGN'] else False

    system_metadata = {
        'status': protocol_definition.status,
        'url': protocol_definition.url,
        'citation': protocol_definition.citation,
        'author': protocol_definition.author,
        'creation_date': protocol_definition.creation_date,
        'updated_date': protocol_definition.updated_date
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

    return Protocol(
        protocol_id,
        protocol_definition.label,
        protocol_definition.machine_code,
        has_custom_ui,
        protocol_definition.description,
        protocol_definition.version,
        out_metadata
    )

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
