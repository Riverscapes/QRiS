-- Create non-spatial tables
CREATE TABLE designs (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    design_name TEXT,
    design_geometry TEXT,
    design_status TEXT,
    design_description TEXT,
    created DATETIME
);

CREATE TABLE structure_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    structure_type_name TEXT,
    structure_mimics TEXT,
    construction_description TEXT,
    function_description TEXT,
    typical_posts INTEGER,
    typical_length NUMERIC,
    typical_width NUMERIC,
    typical_height NUMERIC,
    created DATETIME
);

CREATE TABLE phases (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_name TEXT,
    dominate_action TEXT,
    implementation_date DATE,
    phase_description TEXT,
    created DATETIME
);

-- Add foriegn keys and relationships
ALTER TABLE zoi ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE complexes ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;

-- Add date created fields to spatial tables
ALTER TABLE zoi ADD COLUMN created DATETIME;
ALTER TABLE complexes ADD COLUMN created DATETIME;
ALTER TABLE structure_points ADD COLUMN created DATETIME;
ALTER TABLE structure_lines ADD COLUMN created DATETIME;

-- add created triggers across the board
CREATE TRIGGER designs_after_insert
  AFTER INSERT ON designs
BEGIN
  UPDATE designs
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER zoi_after_insert
  AFTER INSERT ON zoi
BEGIN
  UPDATE zoi
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER complexes_after_insert
  AFTER INSERT ON complexes
BEGIN
  UPDATE complexes
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER structure_lines_after_insert
  AFTER INSERT ON structure_lines
BEGIN
  UPDATE structure_lines
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER structure_points_after_insert
  AFTER INSERT ON structure_points
BEGIN
  UPDATE structure_points
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER structure_types_after_insert
  AFTER INSERT ON structure_types
BEGIN
  UPDATE structure_types
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

CREATE TRIGGER phases_after_insert
  AFTER INSERT ON phases
BEGIN
  UPDATE phases
  SET created = STRFTIME('%Y-%m-%dT%H:%M:%S','NOW')
  WHERE fid = NEW.fid;
END;

-- add modified triggers across the board
-- CREATE TRIGGER designs_after_update
-- AFTER UPDATE ON designs
-- BEGIN
--    UPDATE designs
--    SET modified = STRFTIME('%Y-%m-%dT%H:%M:%S', 'NOW')
--    WHERE fid = NEW.fid;
-- END;

-- Add tables to the geopackages contents table so they are revealed in QGIS
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("designs", "attributes", "designs", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_types", "attributes", "structure_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("phases", "attributes", "phases", 0);

-- Populate some starting structure types
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (1, "BDA Large", "Beaver Dam");
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (2, "BDA Small", "Beaver Dam");
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (3, "BDA Postless", "Beaver Dam");
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (4, "PALS Mid-Channel", "Woody Debris");
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (5, "PALS Bank Attached", "Woody Debris");
INSERT INTO structure_types (fid, structure_type_name, structure_mimics) VALUES (6, "Wood Jam", "Woody Debris");

-- populate some phase values
INSERT INTO phases (fid, phase_name, dominate_action) VALUES (1, "Pilot", "New Structure Additions");
INSERT INTO phases (fid, phase_name, dominate_action) VALUES (2, "Phase 1", "New Structure Additions");
INSERT INTO phases (fid, phase_name, dominate_action) VALUES (3, "Phase 2", "New Structure Additions");

