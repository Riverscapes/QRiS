import json
import sqlite3
from .db_item import DBItem, dict_factory, get_unique_name
from .datespec import DateSpec

EVENT_MACHINE_CODE = 'Event'


class Event(DBItem):

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

        super().__init__('data_capture_events', id, name)
        self.description = description
        self.start = start
        self.end = end
        self.date_text = date_text
        self.event_type = event_type
        self.platform = platform
        self.protocols = protocols.copy() if protocols else []
        self.basemaps = basemaps.copy() if basemaps else []
        self.metadata = metadata

    def update(self, curs: sqlite3.Cursor, name: str, description: str, basemaps: dict):

        curs.execute('UPDATE events SET name = ?, description = ? WHERE id = ?', [name, description, self.id])

        unused_basemap_ids = []
        curs.execute('SELECT basemap_id FROM event_basemaps WHERE event_id = ?', self.id)
        for row in curs.fetchall():
            if row['id'] not in basemaps.keys():
                unused_basemap_ids.append((self.id, row['basemap_id']))

        if len(unused_basemap_ids) > 0:
            curs.executemany('DELETE FROM event_basemaps where event_id = ? and basemap_id = ?', self.id, unused_basemap_ids)

        curs.executemany('INSERT INTO event_basemaps (event_id, basemap_id) VALUES (?, ?) ON CONFLICT(event_id, basemap_id) DO NOTHING', [self.id, basemaps.keys()])

        self.name = name
        self.description = description
        self.basemaps = basemaps


def load(curs: sqlite3.Cursor, protocols: dict, lookups: dict, basemaps: dict) -> dict:

    curs.execute('SELECT * FROM events')
    events = {row['id']: Event(
        row['id'],
        row['name'],
        row['description'],
        DateSpec(row['start_year'], row['start_month'], row['start_day']),
        DateSpec(row['end_year'], row['end_month'], row['end_day']),
        row['date_text'],
        lookups['lkp_event_types'][row['event_type_id']],
        lookups['lkp_platform'][row['platform_id']],
        json.loads(row['metadata']) if row['metadata'] else None,
        None,
        None
    ) for row in curs.fetchall()}

    for event in events.values():

        curs.execute('SELECT * FROM event_protocols WHERE event_id = ?', [event.id])
        event.protocols = [protocols[row['protocol_id']] for row in curs.fetchall()]

        curs.execute('SELECT * FROM event_basemaps WHERE event_id = ?', [event.id])
        event.basemaps = [basemaps[row['basemap_id']] for row in curs.fetchall()]

    return events


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
