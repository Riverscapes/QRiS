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
        super().__init__('attachments', id, display_label)

        self.id = id
        self.name = display_label
        self.fc_name = 'attachments'
        self.path = path
        self.attachment_type = attachment_type
        self.description = description
        self.metadata = metadata if metadata is not None else {}
        self.icon = 'link' if self.attachment_type == Attachment.TYPE_WEB_LINK else 'file'

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
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex
            
    def project_path(self, project_file: str) -> str:
        attachments_dir = attachments_path(project_file)
        return parse_posix_path(os.path.join(attachments_dir, self.path))

    def delete(self, db_path: str) -> None:
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('DELETE FROM attachments WHERE attachment_id = ?', [self.id])
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise ex

        # Optionally, delete the file if it exists
        if os.path.exists(self.path):
            os.remove(self.path)

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
