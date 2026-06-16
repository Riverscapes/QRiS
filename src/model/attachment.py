import os
import json
import sqlite3
from typing import Dict

from .db_item import DBItem
from ..QRiS.path_utilities import parse_posix_path


ATTACHMENT_MACHINE_CODE = 'Attachment'

class Attachment(DBItem):
    
    TYPE_FILE = 'file'
    TYPE_WEB_LINK = 'weblink'

    def __init__(self, id: int, display_label: str, path: str, attachment_type: str, description: str = None, metadata: dict = None):
        super().__init__('attachments', id, display_label, metadata)

        self.id = id
        self.name = display_label
        self.fc_name = 'attachments'
        self.path = path
        self.attachment_type = attachment_type
        self.description = description
        self.icon = 'link' if self.attachment_type == Attachment.TYPE_WEB_LINK else 'file'

    def set_metadata(self, metadata: dict) -> None:
        super().set_metadata(metadata)
        self.date = self.system_metadata.get('date', None)
        self.attachment_type_label = self.system_metadata.get('attachment_type_label', None)

    def update(self, db_path: str, display_label: str, path: str = None, description: str = None, metadata: dict = None) -> None:
        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        out_path = path if path is not None else self.path

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE attachments SET display_label = ?, path = ?, description = ?, metadata = ? WHERE attachment_id = ?',
                             [display_label, out_path, description, metadata_str, self.id])
                conn.commit()

                self.name = display_label
                self.path = out_path
                self.description = description
                self.set_metadata(metadata)

            except Exception as ex:
                conn.rollback()
                raise ex
            
    def attachment_path(self, project_file: str) -> str:
        attachments_dir = attachments_path(project_file)
        return parse_posix_path(os.path.join(attachments_dir, self.path))

    def delete(self, db_path: str) -> None:
        # Resolve the full path before removing from the DB
        full_path = self.attachment_path(db_path) if self.attachment_type == Attachment.TYPE_FILE else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('DELETE FROM attachments WHERE attachment_id = ?', [self.id])
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise ex

        if full_path is not None and os.path.exists(full_path):
            os.remove(full_path)

def load_attachments(cursor: sqlite3.Cursor) -> Dict[int, Attachment]:
    attachments = {}
    cursor.execute('SELECT attachment_id, attachment_type, display_label, path, description, metadata FROM attachments')
    for row in cursor.fetchall():
        attachment_id, attachment_type, display_label, path, description, metadata_str = row.values()
        metadata = json.loads(metadata_str) if metadata_str else {}
        attachments[attachment_id] = Attachment(id=attachment_id, display_label=display_label, path=path, attachment_type=attachment_type, description=description, metadata=metadata)
    return attachments

def insert_attachment(db_path: str, display_label: str, path: str, attachment_type: str, description: str = None, metadata: dict = None) -> Attachment:
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None

    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute('INSERT INTO attachments (display_label, path, attachment_type, description, metadata) VALUES (?, ?, ?, ?, ?)',
                     [display_label, path, attachment_type, description, metadata_str])
        conn.commit()
        attachment_id = curs.lastrowid

    return Attachment(id=attachment_id, display_label=display_label, path=path, attachment_type=attachment_type, description=description, metadata=metadata)

def attachments_path(project_file: str) -> str:
    """Get the attachments directory path for the given project file."""
    return parse_posix_path(os.path.join(os.path.dirname(project_file), 'attachments'))


def load_dce_attachments(db_path: str, event_id: int) -> Dict[int, tuple]:
    """
    Return all attachments associated with the given DCE event.
    Returns a dict of attachment_id -> (Attachment, association_metadata dict).
    association_metadata may include 'purpose' and any other per-association fields.
    """
    result = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        curs = conn.cursor()
        curs.execute('''
            SELECT a.attachment_id, a.attachment_type, a.display_label, a.path, a.description, a.metadata,
                   da.metadata AS assoc_metadata
            FROM attachments a
            JOIN dce_attachments da ON da.attachment_id = a.attachment_id
            WHERE da.event_id = ?
        ''', [event_id])
        for row in curs.fetchall():
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            assoc_metadata = json.loads(row['assoc_metadata']) if row['assoc_metadata'] else {}
            attachment = Attachment(
                id=row['attachment_id'],
                display_label=row['display_label'],
                path=row['path'],
                attachment_type=row['attachment_type'],
                description=row['description'],
                metadata=metadata
            )
            result[row['attachment_id']] = (attachment, assoc_metadata)
    return result

def associate_attachment_with_dce(db_path: str, event_id: int, attachment_id: int, purpose: str = None) -> None:
    """Create (or update) an association between an attachment and a DCE event."""
    assoc_metadata = json.dumps({'purpose': purpose}) if purpose else None
    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute(
            'INSERT OR REPLACE INTO dce_attachments (event_id, attachment_id, metadata) VALUES (?, ?, ?)',
            [event_id, attachment_id, assoc_metadata]
        )
        conn.commit()

def disassociate_attachment_from_dce(db_path: str, event_id: int, attachment_id: int) -> None:
    """Remove the association between an attachment and a DCE event (does not delete the attachment)."""
    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute(
            'DELETE FROM dce_attachments WHERE event_id = ? AND attachment_id = ?',
            [event_id, attachment_id]
        )
        conn.commit()

def load_events_for_attachment(db_path: str, attachment_id: int) -> list:
    """
    Return a list of (event_id, event_name, purpose) tuples
    for all DCE events that reference the given attachment.
    """
    results = []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        curs = conn.cursor()
        curs.execute('''
            SELECT e.id, e.name, e.metadata, da.metadata AS assoc_metadata
            FROM events e
            JOIN dce_attachments da ON da.event_id = e.id
            WHERE da.attachment_id = ?
            ORDER BY e.name
        ''', [attachment_id])
        for row in curs.fetchall():
            assoc_metadata = json.loads(row['assoc_metadata']) if row['assoc_metadata'] else {}
            purpose = assoc_metadata.get('purpose', '') or ''

            results.append((row['id'], row['name'], purpose))
    return results
