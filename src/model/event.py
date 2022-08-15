import json
import sqlite3

from .event_layer import EventLayer
from .db_item import DBItem, dict_factory, update_intersect_table
from .datespec import DateSpec

EVENT_MACHINE_CODE = 'Event'

# Database ID of the design event type. Used to determine which icon to use
DESIGN_EVENT_TYPE_ID = 2


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
                 protocols: list,
                 basemaps: list,
                 metadata: dict):

        super().__init__('events', id, name)
        self.description = description
        self.start = start
        self.end = end
        self.date_text = date_text
        self.event_type = event_type
        self.platform = platform
        self.protocols = protocols.copy() if protocols else []
        self.basemaps = basemaps.copy() if basemaps else []
        self.metadata = metadata

        self.icon = 'design' if self.event_type.id == DESIGN_EVENT_TYPE_ID else 'event'

        event_layers = {}
        for protocol in self.protocols:
            for layer in protocol.layers:
                if layer.id not in event_layers:
                    # Note the key is the layer. The id passed into the constructor is that of the Event itself
                    event_layers[layer.id] = EventLayer(id, layer)

        self.event_layers = list(event_layers.values())

    def update(self, db_path: str, name: str, description: str, protocols: list, basemaps: list, start_date: DateSpec, end_date: DateSpec, platform: DBItem):

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            try:
                curs.execute('UPDATE events SET name = ?, description = ?, platform_id = ?, start_year = ?, start_month = ?, start_day = ?, end_year = ?, end_month = ?, end_day = ? WHERE id = ?',
                             [name, description, platform.id, start_date.year, start_date.month, start_date.day, end_date.year, end_date.month, end_date.day, self.id])

                update_intersect_table(curs, 'event_basemaps', 'event_id', 'basemap_id', self.id, [item.id for item in basemaps])
                update_intersect_table(curs, 'event_protocols', 'event_id', 'protocol_id', self.id, [item.id for item in protocols])

                self.name = name
                self.description = description
                self.basemaps = basemaps
                self.protocols = protocols
                self.start = start_date
                self.end = end_date
                self.platform = platform
                conn.commit()

            except Exception as ex:
                conn.rollback()
                raise ex


def load(curs: sqlite3.Cursor, protocols: dict, lookups: dict, basemaps: dict) -> dict:

    curs.execute('SELECT * FROM event_protocols')
    event_protocols = [(row['event_id'], protocols[row['protocol_id']]) for row in curs.fetchall()]

    curs.execute('SELECT * FROM event_basemaps')
    event_basemaps = [(row['event_id'], basemaps[row['basemap_id']]) for row in curs.fetchall()]

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
        [protocol for event_id, protocol in event_protocols if event_id == row['id']],
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
           protocols: list,
           basemaps: list,
           metadata: dict) -> Event:

    description = description if description and len(description) > 0 else None
    basemaps = basemaps or []
    protocols = protocols or []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()

        try:
            curs.execute("""INSERT INTO events (
                name,
                description,
                event_type_id,
                platform_id,
                metadata,
                date_text,
                start_year,
                start_month,
                start_day,
                end_year,
                end_month,
                end_day
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
                name,
                description,
                event_type.id,
                platform.id,
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

            curs.executemany('INSERT INTO event_protocols (event_id, protocol_id) VALUES (?, ?)', [(event_id, protocol.id) for protocol in protocols])
            curs.executemany('INSERT INTO event_basemaps (event_id, basemap_id) VALUES (?, ?)', [(event_id, basemap.id) for basemap in basemaps])

            event = Event(event_id, name, description, start, end, date_text, event_type, platform, protocols, basemaps, metadata)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return event
