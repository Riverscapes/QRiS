import json
import sqlite3
from typing import List, Dict, Tuple

# from .event_layer import EventLayer
from .db_item import DBItem, dict_factory, update_intersect_table
from .datespec import DateSpec
from .layer import Layer
from .event_layer import EventLayer
from .raster import Raster
EVENT_MACHINE_CODE = 'Event'

# Database ID of the design event type. Used to determine which icon to use
DESIGN_EVENT_TYPE_ID = 2
AS_BUILT_EVENT_TYPE_ID = 3


class Event(DBItem):
    """ Data Capture Event class"""

    def __init__(self,
                 id: int,
                 name: str,
                 description: str,
                 start: DateSpec,
                 end: DateSpec,
                 date_text: str,
                 event_type: DBItem,
                 platform: DBItem,
                 representation: DBItem,
                 event_layers: List[EventLayer],
                 rasters: List[Raster],
                 metadata: dict):

        super().__init__('events', id, name)
        self.description = description
        self.start = start
        self.end = end
        self.date_text = date_text
        self.event_type = event_type
        self.platform = platform
        self.representation = representation
        self.event_layers = event_layers
        self.rasters = rasters.copy() if rasters else []
        self.metadata = metadata

        self.icon = 'design' if self.event_type.id == DESIGN_EVENT_TYPE_ID else 'event'

    def update(self, db_path: str, name: str, description: str, layers: List[Layer], rasters: list, start_date: DateSpec, end_date: DateSpec, platform: DBItem, representation: DBItem, metadata: dict) -> None:

        sql_description = description if description is not None and len(description) > 0 else None
        sql_metadata = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            try:
                curs.execute("""
                UPDATE events SET
                    name = ?,
                    description = ?,
                    platform_id = ?,
                    representation_id = ?,
                    start_year = ?,
                    start_month = ?,
                    start_day = ?,
                    end_year = ?,
                    end_month = ?,
                    end_day = ?,
                    metadata = ?
                WHERE id = ?""",
                             [name, sql_description, platform.id, representation.id, start_date.year, start_date.month, start_date.day, end_date.year, end_date.month, end_date.day, sql_metadata, self.id])

                update_intersect_table(curs, 'event_rasters', 'event_id', 'raster_id', self.id, [item.id for item in rasters])

                self.name = name
                self.description = description
                self.basemaps = rasters
                save_event_layers(curs, self.id, layers, self.event_layers)
                self.start = start_date
                self.end = end_date
                self.platform = platform
                self.representation = representation
                self.metadata = metadata
                conn.commit()

            except Exception as ex:
                conn.rollback()
                raise ex


def load(curs: sqlite3.Cursor, protocols: dict, methods: dict, layers: dict, lookups: dict, rasters: dict) -> Dict[int, Event]:

    # curs.execute('SELECT * FROM event_protocols')
    # event_protocols = [(row['event_id'], protocols[row['protocol_id']]) for row in curs.fetchall()]

    curs.execute('SELECT * FROM event_rasters')
    event_basemaps = [(row['event_id'], rasters[row['raster_id']]) for row in curs.fetchall()]

    curs.execute('SELECT * FROM event_layers')
    event_layers = [EventLayer(row['id'], row['event_id'], layers[row['layer_id']]) for row in curs.fetchall()]

    curs.execute('SELECT * FROM events')
    return {row['id']: Event(
        row['id'],
        row['name'],
        row['description'],
        DateSpec(row['start_year'], row['start_month'], row['start_day']),
        DateSpec(row['end_year'], row['end_month'], row['end_day']),
        row['date_text'],
        lookups['lkp_event_types'][row['event_type_id']],
        lookups['lkp_platform'][row['platform_id']],
        lookups['lkp_representation'][row['representation_id']],
        [event_layer for event_layer in event_layers if event_layer.event_id == row['id']],
        [basemap for event_id, basemap in event_basemaps if event_id == row['id']],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


def insert(db_path: str,
           name: str,
           description: str,
           start: DateSpec,
           end: DateSpec,
           date_text: str,
           event_type: DBItem,
           platform: DBItem,
           representation: DBItem,
           layers: List[Layer],
           rasters: list,
           metadata: dict) -> Event:
    """
    Layers is a list of Layers objects that are in use for this event"""

    description = description if description and len(description) > 0 else None
    rasters = rasters or []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()

        try:
            curs.execute("""INSERT INTO events (
                name,
                description,
                event_type_id,
                platform_id,
                representation_id,
                metadata,
                date_text,
                start_year,
                start_month,
                start_day,
                end_year,
                end_month,
                end_day
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
                name,
                description,
                event_type.id,
                platform.id,
                representation.id,
                json.dumps(metadata) if metadata else None,
                date_text if date_text else None,
                start.year,
                start.month,
                start.day,
                end.year,
                end.month,
                end.day
            ])
            event_id = curs.lastrowid

            curs.executemany('INSERT INTO event_rasters (event_id, raster_id) VALUES (?, ?)', [(event_id, raster.id) for raster in rasters])

            event_layers = []
            for layer in layers:
                curs.execute('INSERT INTO event_layers (event_id, layer_id) VALUES (?, ?)', [event_id, layer.id])
                event_layers.append(EventLayer(curs.lastrowid, event_id, layer))

            event = Event(event_id, name, description, start, end, date_text, event_type, platform, representation, event_layers, rasters, metadata)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return event


def save_event_layers(curs: sqlite3.Cursor, event_id: int, layers: List[Layer], event_layers: List[EventLayer]) -> None:
    """ Used by both the INSERT and UPDATE operations
    When used from INSERT it obviously should not find any existing event layers."""

    # Identify unused layers
    unused_event_layers = []
    curs.execute('SELECT id, layer_id FROM event_layers WHERE event_id = ?', [event_id])
    for row in curs.fetchall():
        in_use = False
        for layer in layers:
            if row['layer_id'] == layer.id:
                in_use = True
                break

        if in_use is False:
            for event_layer in event_layers:
                if event_layer.id == row['id']:
                    unused_event_layers.append(event_layer)

    # Finally delete the event layer from the database and remove it from the events list of event layers
    curs.executemany('DELETE FROM Event_layers WHERE id = ?', [event_layer.id for event_layer in unused_event_layers])
    [event_layers.remove(event_layer) for event_layer in unused_event_layers]

    # Upsert new event layers and add any new ones to the list
    for layer in layers:
        curs.execute('INSERT INTO event_layers (event_id, layer_id) VALUES (?, ?) ON CONFLICT (event_id, layer_id) DO NOTHING', [event_id, layer.id])
        if curs.lastrowid != 0:
            event_layers.append(EventLayer(curs.lastrowid, event_id, layer))
