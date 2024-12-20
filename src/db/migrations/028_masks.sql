-- sqlite 

-- Create new sample frame types table
CREATE TABLE sample_frame_types (
    id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add the new sample frame types
INSERT INTO sample_frame_types (id, name, description, metadata) VALUES (1, 'sample_frame', 'Sample Frame', '{}');
INSERT INTO sample_frame_types (id, name, description, metadata) VALUES (2, 'aoi', 'Area of Interest', '{}');
INSERT INTO sample_frame_types (id, name, description, metadata) VALUES (3, 'valley_bottom', 'Valley Bottom', '{}');

-- Add sample_frame_type_id to sample frames that references the sample_frame_types table
ALTER TABLE sample_frames ADD COLUMN sample_frame_type_id INTEGER REFERENCES sample_frame_types(id);

-- the current sample frames are all sample_frame type
UPDATE sample_frames SET sample_frame_type_id = 1;

-- copy the aois from the masks table to the sample_frames table
INSERT INTO sample_frames (name, description, metadata, sample_frame_type_id)
    SELECT name, description, json_set(IFNULL(metadata, '{}'), '$.old_primary_key', id), 2 FROM masks;

-- copy the features from aoi_features to sample_frame_features, and update the sample_frame_id to the new sample_frame_id
INSERT INTO sample_frame_features (geom, sample_frame_id, metadata)
    SELECT AOIF.geom, SF.id, AOIF.metadata
    FROM aoi_features AOIF
    INNER JOIN sample_frames SF ON AOIF.mask_id = json_extract(SF.metadata, '$.old_primary_key');

-- drop the old primary key from the metadata
UPDATE sample_frames SET metadata = json_remove(metadata, '$.old_primary_key');

-- repeat for valley bottoms
INSERT INTO sample_frames (name, description, metadata, sample_frame_type_id)
    SELECT name, description, json_set(IFNULL(metadata, '{}'), '$.old_primary_key', id), 3 FROM valley_bottoms;

-- copy the features from valley_bottom_features to sample_frame_features, and update the sample_frame_id to the new sample_frame_id
INSERT INTO sample_frame_features (geom, sample_frame_id, metadata)
    SELECT VBF.geom, SF.id, VBF.metadata
    FROM valley_bottom_features VBF
    INNER JOIN sample_frames SF ON VBF.valley_bottom_id = json_extract(SF.metadata, '$.old_primary_key');

-- drop the old primary key from the metadata
UPDATE sample_frames SET metadata = json_remove(metadata, '$.old_primary_key');

-- drop the tables
DROP TABLE valley_bottom_features;
DROP TABLE valley_bottoms;
DROP TABLE mask_features;
DROP TABLE aoi_features;
DROP TABLE masks;

-- remove the entires for gpkg_contents and gpkg_geometry_columns
DELETE FROM gpkg_geometry_columns WHERE table_name IN ('aoi_features', 'mask_features', 'valley_bottom_features');
DELETE FROM gpkg_contents WHERE table_name IN ('aoi_features', 'masks', 'valley_bottom_features', 'valley_bottoms', 'mask_features');
