-- Create the new sample frames table
CREATE TABLE sample_frames(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('sample_frames', 'attributes', 'sample_frames', 0);

-- Alter the sample frames feature class to include the new fields
ALTER TABLE sample_frame_features ADD COLUMN sample_frame_id INTEGER REFERENCES sample_frames(id) ON DELETE CASCADE;
ALTER TABLE sample_frame_features ADD COLUMN display_label TEXT;
ALTER TABLE sample_frame_features ADD COLUMN flow_path TEXT;
ALTER TABLE sample_frame_features ADD COLUMN flows_into INTEGER;
ALTER TABLE sample_frame_features ADD COLUMN metadata TEXT;

CREATE INDEX ix_sample_frame_features_sample_frame_id ON sample_frame_features(sample_frame_id);
CREATE INDEX ix_sample_frame_features_flows_into ON sample_frame_features(flows_into);
CREATE INDEX ix_sample_frame_features_flow_path ON sample_frame_features(flow_path);

-- Now fix the metric values table to remove the old mask_features references
DROP TABLE metric_values;

CREATE TABLE metric_values (
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    sample_frame_feature_id INTEGER REFERENCES sample_frame_features(fid) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES metrics(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
--     metric_source_id INTEGER REFERENCES metric_sources(id) ON DELETE CASCADE,
    manual_value NUMERIC,
    automated_value NUMERIC,
    is_manual INT NOT NULL DEFAULT 1,
    metadata TEXT,
    description TEXT,
    uncertainty NUMERIC,
    unit_id INTEGER REFERENCES lkp_units(id),
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_metric_values PRIMARY KEY (analysis_id, event_id, sample_frame_feature_id, metric_id)
);

CREATE INDEX fx_metric_values_analysis_id ON metric_values(analysis_id);
CREATE INDEX fx_metric_values_sample_frame_feature_id ON metric_values(sample_frame_feature_id);
CREATE INDEX fx_metric_values_metric_id ON metric_values(metric_id);
CREATE INDEX fx_metric_values_event_id ON metric_values(event_id);
