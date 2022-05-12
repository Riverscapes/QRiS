-- Create lookup tables these values should not change....EVER!!!!
CREATE TABLE lkp_design_status (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_design_status (fid, name, description) VALUES (1, "Specification", "Design is a specification of structure locations and types that may be built in the future");
INSERT INTO lkp_design_status (fid, name, description) VALUES (2, "As-Built", "Design is a representation of structure locations and types that have been built");


CREATE TABLE lkp_structure_mimics (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_mimics (fid, name, description) VALUES (1, "Beaver Dam", "Structure has been designed to mimic the form and function of a beaver dam");
INSERT INTO lkp_structure_mimics (fid, name, description) VALUES (2, "Wood Jam", "Structure has been designed to mimic the form and function of a wood jam or piece of woody debris");
INSERT INTO lkp_structure_mimics (fid, name, description) VALUES (3, "Other", "Structure does not mimic a beaver dam, wood jam, or woody debris");


CREATE TABLE lkp_phase_action (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_phase_action (fid, name, description) VALUES (1, "New Structure Additions", "Phase implementation primarily consists of new structure construction");
INSERT INTO lkp_phase_action (fid, name, description) VALUES (2, "Existing Structure Enhancements", "Phase implementation primarily consists of enhancing the materials and dimensions of existing structures");
INSERT INTO lkp_phase_action (fid, name, description) VALUES (3, "Other", "Phase implementation consists of other implementation actions");

CREATE TABLE lkp_zoi_stage (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_zoi_stage (fid, name, description) VALUES (1, "Baseflow", "Extent is the expected influence during or in response to baseflow discharge");
INSERT INTO lkp_zoi_stage (fid, name, description) VALUES (2, "Typical Flood", "Extent is the expected influence during or in response to a typical flood event (e.g., 5 year recurrence interval)");
INSERT INTO lkp_zoi_stage (fid, name, description) VALUES (3, "Large Flood", "Extent the expected influence during or in response to a large flood event (e.g., 20 year recurrence interval)");
INSERT INTO lkp_zoi_stage (fid, name, description) VALUES (4, "Other", "Extent is not related to flood event");

-- Create non-spatial tables
CREATE TABLE designs (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    name TEXT,
    structure_geometry TEXT,
    status_id INTEGER REFERENCES lkp_design_status(fid) ON DELETE CASCADE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE structure_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mimics_id INTEGER REFERENCES lkp_structure_mimics(fid) ON DELETE CASCADE,
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
INSERT INTO structure_types (fid, name, mimics_id) VALUES (7, "Other", 3);

CREATE TABLE zoi_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TODO Get abbreviated descriptions from the manual.
INSERT INTO zoi_types (fid, name, description) VALUES (1, "Increase Channel Complexity", "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment");
INSERT INTO zoi_types (fid, name, description) VALUES (2, "Accelerate Incision Recovery", "Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation");
INSERT INTO zoi_types (fid, name, description) VALUES (3, "Lateral Channel Migration", "Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders");
INSERT INTO zoi_types (fid, name, description) VALUES (4, "Increase Floodplain Connectivity", "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow");
INSERT INTO zoi_types (fid, name, description) VALUES (5, "Facilitate Beaver Translocation", "Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation");
INSERT INTO zoi_types (fid, name, description) VALUES (6, "Other", "Area of hydraulic feature creation (e.g., eddy, shear zone, hydraulic jet)");

CREATE TABLE phases (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    primary_action_id INTEGER REFERENCES lkp_phase_action(fid) ON DELETE CASCADE,
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
ALTER TABLE zoi ADD COLUMN influence_type_id INTEGER REFERENCES zoi_types(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN stage_id INTEGER REFERENCES lkp_zoi_stage(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN description TEXT;
ALTER TABLE zoi ADD COLUMN created DATETIME;


ALTER TABLE complexes ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE complexes ADD COLUMN description TEXT;
ALTER TABLE complexes ADD COLUMN initial_condition TEXT;
ALTER TABLE complexes ADD COLUMN target_condition TEXT;
ALTER TABLE complexes ADD COLUMN created DATETIME;


ALTER TABLE structure_lines ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN name TEXT;
ALTER TABLE structure_lines ADD COLUMN description TEXT;
ALTER TABLE structure_lines ADD COLUMN created DATETIME;


ALTER TABLE structure_points ADD COLUMN design_id INTEGER REFERENCES designs(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN phase_id INTEGER REFERENCES phases(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN name TEXT;
ALTER TABLE structure_points ADD COLUMN description TEXT;
ALTER TABLE structure_points ADD COLUMN created DATETIME;


-- Add table names to the geopackages contents table so they are revealed in QGIS
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_structure_mimics", "attributes", "lkp_structure_mimics", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_zoi_stage", "attributes", "lkp_zoi_stage", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_phase_action", "attributes", "lkp_phase_action", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_design_status", "attributes", "lkp_design_status", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("designs", "attributes", "designs", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_types", "attributes", "structure_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("zoi_types", "attributes", "zoi_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("phases", "attributes", "phases", 0);
