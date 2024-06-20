-- Valley Bottoms
CREATE TABLE valley_bottoms
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE valley_bottom_features ADD COLUMN valley_bottom_id INTEGER REFERENCES valley_bottoms(id) ON DELETE CASCADE;
ALTER TABLE valley_bottom_features ADD COLUMN description TEXT;
ALTER TABLE valley_bottom_features ADD COLUMN metadata TEXT;