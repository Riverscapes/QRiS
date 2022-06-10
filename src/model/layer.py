import sqlite3
from .db_item import DBItem


class Layer(DBItem):
    """Represents the definition of a layer that can be used by an event protocol.

    This class possesses the properties needed to add the layer to the map (with the addition of
    the event id definition query filter."""

    def __init__(self, id: int, fc_name: str, display_name: str, qml: str, is_lookup: bool, geom_type: str, description: str):
        super().__init__('layers', id, fc_name)
        self.display_name = display_name
        self.qml = qml
        self.is_lookup = is_lookup
        self.geom_type = geom_type
        self.description = description


def load_layers(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM layers')
    return {row['id']: Layer(
        row['id'],
        row['fc_name'],
        row['display_name'],
        row['qml'],
        row['is_lookup'],
        row['geom_type'],
        row['description']
    ) for row in curs.fetchall()}
