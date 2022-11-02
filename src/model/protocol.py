import sqlite3
from .db_item import DBItem


class Protocol(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, has_custom_ui: bool, description: str):
        super().__init__('protocols', id, name)
        self.description = description
        self.machine_code = machine_code
        self.has_custom_ui = has_custom_ui
        self.methods = []
        self.icon = 'protocol'


def load(curs: sqlite3.Cursor, methods: dict) -> dict:

    curs.execute('SELECT * FROM protocols')
    protocols = {row['id']: Protocol(
        row['id'],
        row['name'],
        row['machine_code'],
        row['has_custom_ui'],
        row['description']
    ) for row in curs.fetchall()}

    # Load methods that are part of each protocol
    for protocol in protocols.values():
        curs.execute('SELECT * FROM protocol_methods WHERE protocol_id = ?', [protocol.id])
        [protocol.methods.append(methods[row['method_id']]) for row in curs.fetchall()]

    # Load methods that are not part of any protocol
    curs.execute('SELECT m.id FROM methods m LEFT JOIN protocol_methods pm ON m.id = pm.method_id WHERE pm.method_id IS NULL')
    orphan_method_ids = [row['id'] for row in curs.fetchall()]
    if len(orphan_method_ids) > 0:
        # Create a dummy protocol for these methods
        protocols[-1] = Protocol(
            -1,
            'Methods without a protocol',
            'ORPHAN_METHODS',
            False,
            None
        )

        [protocols[-1].methods.append(methods[method_id]) for method_id in orphan_method_ids]

    return protocols
