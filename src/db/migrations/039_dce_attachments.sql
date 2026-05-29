-- Join table associating project-level attachments with DCEs (events).
-- metadata JSON stores optional per-association fields, e.g. {"purpose": "Final Design"}.
CREATE TABLE IF NOT EXISTS dce_attachments (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    attachment_id INTEGER NOT NULL REFERENCES attachments(attachment_id) ON DELETE CASCADE,
    metadata TEXT,
    PRIMARY KEY (event_id, attachment_id)
);

INSERT INTO gpkg_contents (table_name, data_type, identifier)
VALUES ('dce_attachments', 'attributes', 'dce_attachments');
