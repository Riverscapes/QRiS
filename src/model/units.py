import sqlite3
from .db_item import DBItem


class Unit(DBItem):

    def __init__(self, id: int, name: str, display: str, conversion: float = None, conversion_unit_id: int = None, dimension: str = None):
        super().__init__('units', id, name)
        self.display = display
        self.conversion = conversion
        self.conversion_unit_id = conversion_unit_id
        self.dimension = dimension
        self.icon = 'unit'


def load_units(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM lkp_units')
    return {row['id']: Unit(
        row['id'],
        row['name'],
        str(row['display_name']),
        row['conversion'],
        row['conversion_unit_id'],
        row['dimension']
    ) for row in curs.fetchall()}


def unit_conversion(from_unit: Unit, to_unit: Unit, value: float) -> float:
    if from_unit.id == to_unit.id:
        return 1.0 * value
    elif from_unit.conversion_unit_id == to_unit.id:
        return from_unit.conversion * value
    elif to_unit.conversion_unit_id == from_unit.id:
        return (1.0 / to_unit.conversion) * value
    else:
        raise Exception('Cannot convert units')
