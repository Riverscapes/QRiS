-- Create lookup tables these values should not change....EVER!!!!
CREATE TABLE design_status (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO design_status (fid, name, description) VALUES (1, "Specification", "Design is a specification of structure locations and types that may be built in the future");
INSERT INTO design_status (fid, name, description) VALUES (2, "As-Built", "Design is a representation of structure locations and types that have been built");


CREATE TABLE structure_mimics (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO structure_mimics (fid, name, description) VALUES (1, "Beaver Dam", "Structure has been designed to mimic the form and function of a beaver dam");
INSERT INTO structure_mimics (fid, name, description) VALUES (2, "Wood Jam", "Structure has been designed to mimic the form and function of a wood jam or piece of woody debris");
INSERT INTO structure_mimics (fid, name, description) VALUES (3, "Other", "Structure does not mimic a beaver dam, wood jam, or woody debris");


CREATE TABLE phase_action (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO phase_action (fid, name, description) VALUES (1, "New Structure Additions", "Phase implementation primarily consists of new structure construction");
INSERT INTO phase_action (fid, name, description) VALUES (2, "Existing Structure Enhancements", "Phase implementation primarily consists of enhancing the materials and dimensions of existing structures");
INSERT INTO phase_action (fid, name, description) VALUES (3, "Other", "Phase implementation consists of other implementation actions");

CREATE TABLE zoi_stage (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO zoi_stage (fid, name, description) VALUES (1, "Baseflow", "Extent is the expected influence during or in response to baseflow discharge");
INSERT INTO zoi_stage (fid, name, description) VALUES (2, "Typical Flood", "Extent is the expected influence during or in response to a typical flood event (e.g., 5 year recurrence interval)");
INSERT INTO zoi_stage (fid, name, description) VALUES (3, "Large Flood", "Extent the expected influence during or in response to a large flood event (e.g., 20 year recurrence interval)");
INSERT INTO zoi_stage (fid, name, description) VALUES (4, "Other", "Extent is not related to flood event");


CREATE TABLE zoi_influence (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO zoi_influence (fid, name, description) VALUES (1, "Depositional Zone", "Area of lateral (e.g., point bar development) and/or elevational (mid-channel bar formation) sediment deposition");
INSERT INTO zoi_influence (fid, name, description) VALUES (2, "Erosional Zone", "Area of lateral (e.g., bank erosion) and/or elevational (e.g., pool formation) erosion");
INSERT INTO zoi_influence (fid, name, description) VALUES (3, "Overbank Flow", "Area of overbank flow dispersal onto valley bottom surfaces (e.g., secondary channel formation, disconnected floodplain inundation)");
INSERT INTO zoi_influence (fid, name, description) VALUES (4, "Pond Creation", "Area of pond formation behind a structural element (e.g., BDA, wood jam, BDA structure complex)");
INSERT INTO zoi_influence (fid, name, description) VALUES (5, "Vegetation Response", "Area of vegetation response (e.g., upland vegetation reduction, riparian vegetation expansion, planting treatment footprint)");
INSERT INTO zoi_influence (fid, name, description) VALUES (6, "Hydraulic Feature", "Area of hydraulic feature creation (e.g., eddy, shear zone, hydraulic jet)");

-- Create non-spatial tables
CREATE TABLE designs (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    structure_geometry TEXT,
    status_id INTEGER REFERENCES design_status(fid) ON DELETE CASCADE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE structure_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mimics_id INTEGER REFERENCES structure_mimics(fid) ON DELETE CASCADE,
    construction_description TEXT,
    function_description TEXT,
    typical_posts INTEGER,
    typical_length NUMERIC,
    typical_width NUMERIC,
    typical_height NUMERIC,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Populate some starting structure types. Values can be edited by the user
INSERT INTO structure_types (fid, name, mimics_id) VALUES (1, "BDA Large", 1);
INSERT INTO structure_types (fid, name, mimics_id) VALUES (2, "BDA Small", 1);
INSERT INTO structure_types (fid, name, mimics_id) VALUES (3, "BDA Postless", 1);
INSERT INTO structure_types (fid, name, mimics_id) VALUES (4, "PALS Mid-Channel", 2);
INSERT INTO structure_types (fid, name, mimics_id) VALUES (5, "PALS Bank Attached", 2);
INSERT INTO structure_types (fid, name, mimics_id) VALUES (6, "Wood Jam", 2);

CREATE TABLE phases (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    primary_action_id INTEGER REFERENCES phase_action(fid) ON DELETE CASCADE,
    implementation_date DATE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- starting phase values. These can be edited by the user
INSERT INTO phases (fid, name, primary_action_id) VALUES (1, "Pilot", 1);
INSERT INTO phases (fid, name, primary_action_id) VALUES (2, "Phase 1", 1);
INSERT INTO phases (fid, name, primary_action_id) VALUES (3, "Phase 2", 1);

-- Add foriegn keys and relationships to existing spatial tables
ALTER TABLE zoi ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN influence_id INTEGER REFERENCES zoi_influnece(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN stage_id INTEGER REFERENCES zoi_stage(fid) ON DELETE CASCADE;
ALTER TABLE complexes ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;

-- Add created fields to spatial tables
ALTER TABLE zoi ADD COLUMN created DATETIME;
ALTER TABLE complexes ADD COLUMN created DATETIME;
ALTER TABLE structure_points ADD COLUMN created DATETIME;
ALTER TABLE structure_lines ADD COLUMN created DATETIME;


-- Add table names to the geopackages contents table so they are revealed in QGIS
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_mimics", "attributes", "structure_mimics", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("zoi_stage", "attributes", "zoi_stage", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("zoi_influence", "attributes", "zoi_influence", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("phase_action", "attributes", "phase_action", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("design_status", "attributes", "design_status", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("designs", "attributes", "designs", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_types", "attributes", "structure_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("phases", "attributes", "phases", 0);

-- views
-- CREATE VIEW complex_structure_counts AS
-- SELECT designs.fid AS Design_ID, designs.design_name AS Design_Name, complexes.fid AS Complex_ID, complexes.complex_name AS Complex_Name, COUNT(structure_points.fid) AS Structure_Count
-- FROM structure_points, designs, complexes
-- WHERE st_contains(complexes.geom, structure_points.geom)
-- GROUP BY designs.fid, designs.design_name, complexes.fid, complexes.complex_name
-- ORDER BY designs.design_name, complexes.complex_name DESC;

-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("complex_structure_counts", "attributes", "complex_structure_counts", 0);
