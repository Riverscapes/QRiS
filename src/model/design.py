import json
import sqlite3
from datetime import datetime

from simplejson import loads
from .db_item import DBItem
from .assessment import Assessment, insert_assessment

DESIGN_MACHINE_CODE = 'DESIGN'


class Design(DBItem):

    def __init__(self, assessment: Assessment, id: int, name: str, description: str, date: datetime, status: DBItem):
        super().__init__('assessment_methods', id, name)
        self.description = description
        self.assessement = assessment
        self.status = status
        self.date = date

    def update(self, db_path: str, name: str, description: str, date: datetime, status: DBItem) -> None:

        description = description if len(description) > 0 else None
        metadata = _build_metadata(status, date)

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE assessment_methods SET name = ?, description = ?, metadata = ? WHERE assessment_method_id = ?', [name, description, metadata, self.id])
                conn.commit()

                self.name = name
                self.status = status
                self.date = date
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_designs(curs: sqlite3.Cursor, statuses: dict, assessment: Assessment) -> dict:

    curs.execute("""SELECT am.* FROM assessment_methods am INNER JOIN methods m ON am.method_id = m.fid
        WHERE am.assessment_id = ?
        AND m.fid = ?""", [assessment.id, DESIGN_MACHINE_CODE])

    for row in curs.fetchall():
        assessment_method_id = row['fid']
        metadata = loads(row['metadata']) if row['metadata'] is not None else None
        status = statuses[metadata['statusId']] if 'statusId' in metadata else None
        date = metadata['date'] if 'date' in metadata else None

        assessment.methods[assessment_method_id] = Design(assessment, assessment_method_id, row['name'], row['description'], date, status)


def insert_design(db_path: str, assessment: Assessment, name: str, description: str, date: datetime, status: DBItem) -> Design:

    description = description if len(description) > 0 else None
    metadata = _build_metadata(status, date)

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()

            if assessment is None:
                assessment = insert_assessment(db_path, None, None, None, None)

            curs.execute("""INSERT INTO assessment_methods (assessment_id, method_id, name, description, metadata)
                SELECT  ?, method_id, ?, ?, ? FROM methods WHERE method_id = ?""", [assessment.id, name, description, json.dumps(metadata), DESIGN_MACHINE_CODE])
            id = curs.lastrowid
            mask = Design(assessment, id, name, description, date, status)
            conn.commit()

        except Exception as ex:
            mask = None
            conn.rollback()
            raise ex

    return mask


def _build_metadata(status: DBItem, date: datetime) -> dict:

    return {
        'statusId': status.id if status is not None else None,
        'date': date if date is not None else None
    }
