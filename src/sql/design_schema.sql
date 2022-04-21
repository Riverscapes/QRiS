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
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_structure_mimics", "attributes", "lkp_structure_mimics", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_zoi_stage", "attributes", "lkp_zoi_stage", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_phase_action", "attributes", "lkp_phase_action", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_design_status", "attributes", "lkp_design_status", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("designs", "attributes", "designs", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_types", "attributes", "structure_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("zoi_types", "attributes", "zoi_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("phases", "attributes", "phases", 0);

-- --------------- VIEWS ------------------


-- CREATE VIEW complex_structure_counts AS
-- SELECT designs.fid AS Design_ID, designs.design_name AS Design_Name, complexes.fid AS Complex_ID, complexes.complex_name AS Complex_Name, COUNT(structure_points.fid) AS Structure_Count
-- FROM structure_points, designs, complexes
-- WHERE st_contains(complexes.geom, structure_points.geom)
-- GROUP BY designs.fid, designs.design_name, complexes.fid, complexes.complex_name
-- ORDER BY designs.design_name, complexes.complex_name DESC;

-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("complex_structure_counts", "attributes", "complex_structure_counts", 0);

-- Structures Points Detailed
CREATE VIEW qry_structure_summary_points AS
SELECT MAX(structure_points.FID) AS [Summary ID], designs.name AS [Design Name], lkp_design_status.name AS [Design Status], phases.name AS [Phase Name], structure_types.name AS [Structure Type], lkp_structure_mimics.name AS [Structure Mimics], Count(structure_points.FID) AS [Structure Count]
FROM phases
    INNER JOIN ((lkp_structure_mimics INNER JOIN structure_types ON lkp_structure_mimics.FID = structure_types.mimics_id)
        INNER JOIN (lkp_design_status INNER JOIN (designs INNER JOIN structure_points ON designs.FID = structure_points.design_id) ON lkp_design_status.FID = designs.status_id) ON structure_types.FID = structure_points.structure_type_id) ON phases.FID = structure_points.phase_id
GROUP BY designs.name, lkp_design_status.name, phases.name, structure_types.name, lkp_structure_mimics.name;

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_structure_summary_points", "attributes", "qry_structure_summary_points", 0);


-- Structures Lines Detailed
CREATE VIEW qry_structure_summary_lines AS
SELECT MAX(structure_lines.FID) AS [Summary ID], designs.name AS [Design Name], lkp_design_status.name AS [Design Status], phases.name AS [Phase Name], structure_types.name AS [Structure Type], lkp_structure_mimics.name AS [Structure Mimics], Count(structure_lines.FID) AS [Structure Count], Round(Sum(st_length(structure_lines.geom, false)),1) AS [Total Length]
FROM phases INNER JOIN ((lkp_structure_mimics INNER JOIN structure_types ON lkp_structure_mimics.FID = structure_types.mimics_id) INNER JOIN (lkp_design_status INNER JOIN (designs INNER JOIN structure_lines ON designs.FID = structure_lines.design_id) ON lkp_design_status.FID = designs.status_id) ON structure_types.FID = structure_lines.structure_type_id) ON phases.FID = structure_lines.phase_id
GROUP BY designs.name, lkp_design_status.name, phases.name, structure_types.name, lkp_structure_mimics.name;

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_structure_summary_lines", "attributes", "qry_structure_summary_lines", 0);

-- Complexes by Type Points
CREATE VIEW qry_complexes_by_type_points AS
SELECT Max(structure_points.FID) AS [Summary ID], designs.name AS [Design Name], lkp_design_status.name AS [Design Status], complexes.FID AS [Complex ID], complexes.name AS [Complex Name], structure_types.name AS [Structure Type], lkp_structure_mimics.name AS [Structure Mimics], Count(structure_points.FID) AS [Structure Count]
FROM ((lkp_structure_mimics INNER JOIN structure_types ON lkp_structure_mimics.FID = structure_types.mimics_id) INNER JOIN (lkp_design_status INNER JOIN (designs INNER JOIN structure_points ON designs.FID = structure_points.design_id) ON lkp_design_status.FID = designs.status_id) ON structure_types.FID = structure_points.structure_type_id) INNER JOIN complexes ON designs.FID = complexes.design_id
WHERE st_contains(complexes.geom, structure_points.geom) AND complexes.design_id = structure_points.design_id
GROUP BY designs.name, lkp_design_status.name, complexes.FID, structure_types.name, lkp_structure_mimics.name;

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_complexes_by_type_points", "attributes", "qry_complexes_by_type_points", 0);


-- Complexes By Type Lines
CREATE VIEW qry_complexes_by_type_lines AS
SELECT Max(structure_lines.FID) AS [Summary ID], designs.name AS [Design Name], lkp_design_status.name AS [Design Status], complexes.FID AS [Complex ID], complexes.name AS [Complex Name], structure_types.name AS [Structure Type], lkp_structure_mimics.name AS [Structure Mimics], Count(structure_lines.FID) AS [Structure Count], Round(Sum(st_length(structure_lines.geom, false)),1) AS [Total Length]
FROM ((lkp_structure_mimics INNER JOIN structure_types ON lkp_structure_mimics.FID = structure_types.mimics_id) INNER JOIN (lkp_design_status INNER JOIN (designs INNER JOIN structure_lines ON designs.FID = structure_lines.design_id) ON lkp_design_status.FID = designs.status_id) ON structure_types.FID = structure_lines.structure_type_id) INNER JOIN complexes ON designs.FID = complexes.design_id
WHERE st_contains(complexes.geom, structure_lines.geom) AND complexes.design_id = structure_lines.design_id
GROUP BY designs.name, lkp_design_status.name, complexes.FID, structure_types.name, lkp_structure_mimics.name;

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_complexes_by_type_lines", "attributes", "qry_complexes_by_type_lines", 0);

-- Design Structure Count Points
CREATE VIEW qry_total_structures_points AS
SELECT Max(qry_structure_summary_points.[Summary ID]) AS [Summary ID], qry_structure_summary_points.[Design Name], qry_structure_summary_points.[Design Status], qry_structure_summary_points.[Phase Name], Sum(qry_structure_summary_points.[Structure Count]) AS [Total Structures]
FROM qry_structure_summary_points
GROUP BY qry_structure_summary_points.[Design Name], qry_structure_summary_points.[Design Status], qry_structure_summary_points.[Phase Name];

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_total_structures_points", "attributes", "qry_total_structures_points", 0);

-- Design Structure Count Lines
CREATE VIEW qry_total_structures_lines AS
SELECT Max(qry_structure_summary_lines.[Summary ID]) AS [Summary ID], qry_structure_summary_lines.[Design Name], qry_structure_summary_lines.[Design Status], qry_structure_summary_lines.[Phase Name], Sum(qry_structure_summary_lines.[Structure Count]) AS [Total Structures], Sum(qry_structure_summary_lines.[Total Length]) AS [Total Structure Length]
FROM qry_structure_summary_lines
GROUP BY qry_structure_summary_lines.[Design Name], qry_structure_summary_lines.[Design Status], qry_structure_summary_lines.[Phase Name];

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("qry_total_structures_lines", "attributes", "qry_total_structures_lines", 0);
