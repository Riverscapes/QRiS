import sqlite3
from .db_item import DBItem


class Protocol(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, has_custom_ui: bool, description: str):
        super().__init__('protocols', id, name)
        self.description = description
        self.machine_code = machine_code
        self.has_custom_ui = has_custom_ui
        self.layers = []
        self.icon = 'protocol'


def load(curs: sqlite3.Cursor, layers: dict) -> dict:

    curs.execute('SELECT * FROM protocols')
    protocols = {row['id']: Protocol(
        row['id'],
        row['name'],
        row['machine_code'],
        row['has_custom_ui'],
        row['description']
    ) for row in curs.fetchall()}

    for protocol in protocols.values():
        curs.execute('SELECT * FROM protocol_layers WHERE protocol_id = ?', [protocol.id])
        [protocol.layers.append(layers[row['layer_id']]) for row in curs.fetchall()]

    return protocols
