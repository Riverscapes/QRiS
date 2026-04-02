import sqlite3
from ..model.db_item import dict_factory

def get_project_layouts(project_path):
    """Retrieve all saved layouts from the project database."""
    with sqlite3.connect(project_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        # Check if table exists first (migration might not have run yet if hot-reloading)
        curs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='layouts'")
        if not curs.fetchone():
            return []
            
        curs.execute("SELECT id, name, created_on, last_modified FROM layouts ORDER BY name")
        return curs.fetchall()

def get_layout_xml(project_path, layout_id):
    """Retrieve the XML content for a specific layout."""
    with sqlite3.connect(project_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute("SELECT layout_xml FROM layouts WHERE id = ?", (layout_id,))
        row = curs.fetchone()
        return row['layout_xml'] if row else None

def save_layout(project_path, name, xml_content):
    """Save a layout to the project database."""
    with sqlite3.connect(project_path) as conn:
        curs = conn.cursor()
        # Check if table exists
        curs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='layouts'")
        if not curs.fetchone():
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
            curs.execute("UPDATE layouts SET layout_xml = ?, last_modified = CURRENT_TIMESTAMP WHERE id = ?", (xml_content, row[0]))
        else:
            # Insert new
            curs.execute("INSERT INTO layouts (name, layout_xml) VALUES (?, ?)", (name, xml_content))
            
def delete_layout(project_path, layout_id):
    """Delete a layout from the project database."""
    with sqlite3.connect(project_path) as conn:
        curs = conn.cursor()
        curs.execute("DELETE FROM layouts WHERE id = ?", (layout_id,))
