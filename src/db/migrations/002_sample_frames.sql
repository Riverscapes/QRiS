CREATE TABLE sample_frames(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE sample_frame_features ADD COLUMN sample_frame_id INTEGER REFERENCES sample_frames(id) ON DELETE CASCADE;
ALTER TABLE sample_frame_features ADD COLUMN display_label TEXT;
ALTER TABLE sample_frame_features ADD COLUMN flow_path TEXT;
ALTER TABLE sample_frame_features ADD COLUMN flows_into INTEGER;
ALTER TABLE sample_frame_features ADD COLUMN metadata TEXT;

CREATE INDEX ix_sample_frame_features_sample_frame_id ON sample_frame_features(sample_frame_id);
CREATE INDEX ix_sample_frame_features_flows_into ON sample_frame_features(flows_into);
CREATE INDEX ix_sample_frame_features_flow_path ON sample_frame_features(flow_path);

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('sample_frames', 'attributes', 'sample_frames', 0);
