import json
import sqlite3
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from ..model.db_item import dict_factory

TEMPLATE_TYPE_SLOT = 'slot'


@dataclass
class MapLayout:
    """Domain model for a saved QGIS layout.

    Layouts are intentionally not DBItems because they are not represented in
    the QRiS project tree and do not need DBItem behavior.
    """

    id: int
    name: str
    layout_xml: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_on: Optional[str] = None
    last_modified: Optional[str] = None

    @property
    def template_type(self) -> Optional[str]:
        return self.metadata.get('template_type')

    def is_slot_template(self) -> bool:
        return self.template_type == TEMPLATE_TYPE_SLOT

    @property
    def slot_metadata(self) -> Dict[str, Any]:
        """Convenience alias used by slot-template workflows."""
        return self.metadata

    @classmethod
    def from_row(cls, row: dict) -> 'MapLayout':
        metadata = json.loads(row['metadata']) if row.get('metadata') else {}
        return cls(
            id=row['id'],
            name=row['name'],
            layout_xml=row.get('layout_xml'),
            metadata=metadata,
            created_on=row.get('created_on'),
            last_modified=row.get('last_modified'),
        )


def _layouts_table_exists(curs: sqlite3.Cursor) -> bool:
    curs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='layouts'")
    return curs.fetchone() is not None


def get_project_layouts(project_path, slot_templates_only=False):
    """Retrieve all saved layouts from the project database.

    If *slot_templates_only* is True, only layouts whose metadata declares
    ``template_type == "slot"`` are returned.
    """
    with sqlite3.connect(project_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        # Check if table exists first (migration might not have run yet if hot-reloading)
        if not _layouts_table_exists(curs):
            return []

        curs.execute("SELECT id, name, created_on, last_modified, metadata FROM layouts ORDER BY name")
        rows = curs.fetchall()

    layouts: List[MapLayout] = [MapLayout.from_row(row) for row in rows]
    if slot_templates_only:
        return [layout for layout in layouts if layout.is_slot_template()]
    return layouts

def get_layout_xml(project_path, layout_id):
    """Retrieve the XML content for a specific layout."""
    with sqlite3.connect(project_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute("SELECT layout_xml FROM layouts WHERE id = ?", (layout_id,))
        row = curs.fetchone()
        return row['layout_xml'] if row else None


def get_layout_with_metadata(project_path, layout_id):
    """Retrieve both XML and metadata for a specific layout.

    Returns a ``MapLayout`` instance, or ``None`` if not found.
    """
    with sqlite3.connect(project_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute(
            "SELECT id, name, layout_xml, metadata FROM layouts WHERE id = ?",
            (layout_id,),
        )
        row = curs.fetchone()
    if row is None:
        return None
    return MapLayout.from_row(row)

def save_layout(project_path, name, xml_content, metadata: dict = None):
    """Save a layout to the project database.

    *metadata* is an optional dict (will be JSON-serialised) that carries
    slot-template declarations when ``template_type == "slot"``.
    """
    metadata_str = json.dumps(metadata) if metadata is not None else None
    with sqlite3.connect(project_path) as conn:
        curs = conn.cursor()
        # Check if table exists
        if not _layouts_table_exists(curs):
             # Create table if it doesn't exist (fallback if migration didn't run)
            curs.execute("""
                CREATE TABLE IF NOT EXISTS layouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    layout_xml TEXT NOT NULL,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Check if layout with name exists
        curs.execute("SELECT id FROM layouts WHERE name = ?", (name,))
        row = curs.fetchone()

        if row:
            # Update existing
            if metadata_str is not None:
                curs.execute(
                    "UPDATE layouts SET layout_xml = ?, metadata = ?, last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (xml_content, metadata_str, row[0]),
                )
            else:
                curs.execute(
                    "UPDATE layouts SET layout_xml = ?, last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (xml_content, row[0]),
                )
        else:
            # Insert new
            curs.execute(
                "INSERT INTO layouts (name, layout_xml, metadata) VALUES (?, ?, ?)",
                (name, xml_content, metadata_str),
            )
            
def delete_layout(project_path, layout_id):
    """Delete a layout from the project database."""
    with sqlite3.connect(project_path) as conn:
        curs = conn.cursor()
        curs.execute("DELETE FROM layouts WHERE id = ?", (layout_id,))
