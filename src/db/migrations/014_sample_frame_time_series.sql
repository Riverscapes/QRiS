-- create the table for time series data
CREATE TABLE time_series (
    time_series_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source TEXT,
    url TEXT,
    description TEXT,
    metadata TEXT
    );

-- create the table for sample frame time series data
CREATE TABLE sample_frame_time_series (
    sample_frame_fid INTEGER NOT NULL REFERENCES sample_frame_features(fid) ON DELETE CASCADE ON UPDATE CASCADE,
    time_series_id INTEGER NOT NULL REFERENCES time_series(time_series_id) ON DELETE CASCADE ON UPDATE CASCADE,
    time_value Date NOT NULL,
    value REAL NOT NULL,
    metadata TEXT,
    PRIMARY KEY (sample_frame_fid, time_series_id, time_value)
    );

CREATE INDEX idx_sample_frame_time_series_time_series_id ON sample_frame_time_series(time_series_id);
CREATE INDEX idx_sample_frame_time_series_time_value ON sample_frame_time_series(time_value);
