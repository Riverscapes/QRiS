import json
import sqlite3
from typing import Dict

from .db_item import DBItem, dict_factory
from .event import Event, update_intersect_table


class PlanningContainer(DBItem):
    """ Planning Container class"""

    def __init__(self,
                 id: int,
                 name: str,
                 description: str,
                 planning_events: dict,
                 metadata: dict):

        super().__init__('planning_containers', id, name)
        self.description = description
        self.planning_events = planning_events # dict of event_id and representation_id
        self.metadata = metadata

        self.icon = 'plan'

    def update(self, db_path: str, name: str, description: str, planning_events: dict[Event], metadata: dict) -> None:

        sql_description = description if description is not None and len(description) > 0 else None
        sql_metadata = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            try:
                curs.execute("""
                UPDATE planning_containers SET
                    name = ?,
                    description = ?,
                    metadata = ?
                WHERE id = ?""",
                             [name, sql_description, sql_metadata, self.id])

                update_intersect_table(curs, 'planning_container_events', 'planning_container_id', 'event_id', self.id, [event_id for event_id in planning_events.keys()])
                # now update the table with the representation_id
                curs.executemany('UPDATE planning_container_events SET representation_id = ? WHERE planning_container_id = ? AND event_id = ?', [(representation_id, self.id, event) for event, representation_id in planning_events.items()])
                # drop any events that have a null representation_id
                curs.execute('DELETE FROM planning_container_events WHERE planning_container_id = ? AND representation_id IS NULL', [self.id])

                self.name = name
                self.description = description
                self.planning_events = {event: representation_id for event, representation_id in planning_events.items() if representation_id is not None}
                self.metadata = metadata
                conn.commit()

            except Exception as ex:
                conn.rollback()
                raise ex


def load(curs: sqlite3.Cursor, events: dict) -> Dict[int, PlanningContainer]:

    curs.execute('SELECT * FROM planning_container_events')
    planning_container_events = [(row['planning_container_id'], events[row['event_id']], row['representation_id']) for row in curs.fetchall()]

    curs.execute('SELECT * FROM planning_containers')
    return {row['id']: PlanningContainer(
        row['id'],
        row['name'],
        row['description'],
        {event[1].id: int(event[2]) for event in planning_container_events if event[0] == row['id']},
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


def insert(db_path: str,
           name: str,
           description: str,
           planning_events: dict,
           metadata: dict) -> Event:
    """
    Layers is a list of Event objects that are in use for this planning container"""

    description = description if description and len(description) > 0 else None

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()

        try:
            curs.execute("""INSERT INTO planning_containers (
                name,
                description,
                metadata
            ) VALUES (?, ?, ?)""", [
                name,
                description,
                json.dumps(metadata) if metadata else None
            ])
            planning_container_id = curs.lastrowid

            # drop any events that have a null representation_id
            out_planning_events = {event_id: representation_id for event_id, representation_id in planning_events.items() if representation_id is not None}
            curs.executemany('INSERT INTO planning_container_events (planning_container_id, event_id, representation_id) VALUES (?, ?, ?)', [(planning_container_id, event_id, representation_id) for event_id, representation_id in out_planning_events.items()])

            planning_container = PlanningContainer(planning_container_id, name, description, out_planning_events, metadata)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return planning_container
