import sqlite3
from .db_item import DBItem


class Method(DBItem):

    def __init__(self, id: int, name: str, machine_code: str, description: str):
        super().__init__('methods', id, name)
        self.description = description
        self.machine_code = machine_code
        self.layers = []
        self.icon = 'method'


def load(curs: sqlite3.Cursor, layers: dict) -> dict:

    curs.execute('SELECT * FROM methods')
    methods = {row['id']: Method(
        row['id'],
        row['name'],
        row['machine_code'],
        row['description']
    ) for row in curs.fetchall()}

    for method in methods.values():
        curs.execute('SELECT * FROM method_layers WHERE method_id = ?', [method.id])
        [method.layers.append(layers[row['layer_id']]) for row in curs.fetchall()]

    # Load layers that are not part of any method
    curs.execute('SELECT l.id FROM layers l left join method_layers ml on l.id = ml.layer_id WHERE ml.layer_id IS NULL')
    orphan_ids = [row['id'] for row in curs.fetchall()]

    if len(orphan_ids) > 0:
        methods[-1] = Method(
            -1,
            'Layers that do not belong to a method',
            'ORPHANS',
            None
        )
        [methods[-1].layers.append(layers[layer_id]) for layer_id in orphan_ids]

    return methods
