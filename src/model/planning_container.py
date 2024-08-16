import json
import sqlite3
from typing import List, Dict, Tuple

from .db_item import DBItem, dict_factory
from .event import Event


PLANNING_CONTAINER_MACHINE_CODE = 'Planning Container'
PLANNING_CONTAINER_TYPE_ID = 7

EVENT_PHASES = {1: 'Historic',
                2: 'Current',
                3: 'Future'}


class PlanningContainer(DBItem):
    """ Planning Container class"""

    def __init__(self,
                 id: int,
                 name: str,
                 description: str,
                 planning_events: list,
                 metadata: dict):

        super().__init__('planning_containers', id, name)
        self.description = description
        self.event_type = PLANNING_CONTAINER_TYPE_ID
        self.planning_events = planning_events
        self.metadata = metadata

        # use the start date as text
        # self.date = f'{self.start.year}-{self.start.month}-{self.start.day}' if self.start else None

        self.icon = 'plan'

    def update(self, db_path: str, name: str, description: str, planning_events: List[Event], metadata: dict) -> None:

        sql_description = description if description is not None and len(description) > 0 else None
        sql_metadata = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            try:
                curs.execute("""
                UPDATE planning_container SET
                    name = ?,
                    description = ?,
                    metadata = ?
                WHERE id = ?""",
                             [name, sql_description, sql_metadata, self.id])

                update_intersect_table(curs, 'planning_container_events', 'planning_container_id', 'event_id', self.id, [item.id for item in planning_events])

                self.name = name
                self.description = description
                self.planning_events = planning_events
                self.metadata = metadata
                conn.commit()

            except Exception as ex:
                conn.rollback()
                raise ex


def load(curs: sqlite3.Cursor, events: dict) -> Dict[int, PlanningContainer]:

   
    curs.execute('SELECT * FROM planning_container_events')
    planning_container_events = [(row['planning_container_id'], events[row['event_id']]) for row in curs.fetchall()]

    curs.execute('SELECT * FROM planning_containers')
    return {row['id']: PlanningContainer(
        row['id'],
        row['name'],
        row['description'],
        [event for event in planning_container_events if event[0] == row['id']],
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


def insert(db_path: str,
           name: str,
           description: str,
           planning_events: List[Event],
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
                metadata,
            ) VALUES (?, ?, ?)""", [
                name,
                description,
                json.dumps(metadata) if metadata else None
            ])
            planning_container_id = curs.lastrowid

            curs.executemany('INSERT INTO planning_container_events (planning_container_id, event_id, phase_id) VALUES (?, ?, ?)', [(planning_container_id, event.id) for event in planning_events])

            planning_container = PlanningContainer(planning_container_id, name, description, planning_events, metadata)
            conn.commit()

        except Exception as ex:
            conn.rollback()
            raise ex

    return planning_container

def update_intersect_table(curs: sqlite3.Cursor, table: str, parent_col_name: str, child_col_name: str, parent_id: int, new_child_id_list: list):
    """
    Use this method to refresh an intersect table that consists of just a parent and child ID. See event_basemaps table as an example.
    In this example, the event_id is parent column and the basemap_id is the child."""

    # Determine if there are IDs in the database that are no longer in use (new_child_id_list)
    unused_child_ids = []
    curs.execute(f'SELECT {child_col_name} FROM {table} WHERE {parent_col_name} = ?', [str(parent_id)])

    for row in curs.fetchall():
        if row[child_col_name] not in new_child_id_list:
            unused_child_ids.append((parent_id, row[child_col_name]))

    # Delete those records no longer in use.
    if len(unused_child_ids) > 0:
        curs.executemany(f'DELETE FROM {table} where {parent_col_name} = ? and {child_col_name} = ?', unused_child_ids)

    # Now insert all the records and use NO CONFLICT to skip and duplates that are already there!
    new_ids = [[parent_id, child_id] for child_id in new_child_id_list]
    curs.executemany(f"""INSERT INTO {table} ({parent_col_name}, {child_col_name}) VALUES (?, ?)
        ON CONFLICT({parent_col_name}, {child_col_name}) DO NOTHING""", new_ids)