-- Add attachments table to store project-related files and urls
CREATE TABLE attachments (
    attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attachment_type TEXT NOT NULL,
    display_label TEXT NOT NULL,
    path TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO gpkg_contents (table_name, data_type, identifier)
VALUES ('attachments', 'attributes', 'attachments');