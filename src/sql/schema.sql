-- LOOKUP TABLES
CREATE TABLE  methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- major question is whether a method is specific to the type of geometry used?
-- methods could also be specific to whether the survey is being conducted in the field or on the desktop.
INSERT INTO methods (fid, name,  description) VALUES (1, 'RIM', 'Riverscape Inundation Mapping');
INSERT INTO methods (fid, name,  description) VALUES (2, 'Riverscape Units', 'Placeholder name for the streams need space stupidity');
INSERT INTO methods (fid, name,  description) VALUES (3, 'Low-Tech Design', 'Documentation of a design or as-built low-tech structures');
INSERT INTO methods (fid, name,  description) VALUES (4, 'Structural Elements', 'Survey of primary structural element types');
INSERT INTO methods (fid, name,  description) VALUES (5, 'Geomorphic Units', 'In-channel geomorphic unit survey, could be out of channel as well, who fricken knows');
INSERT INTO methods (fid, name,  description) VALUES (6, 'Geomorphic Units - Extents', 'In-channel geomorphic unit survey, could be out of channel as well, who fricken knows');


CREATE TABLE  metric_sources (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metric_sources (fid, name,  description) VALUES (1, 'Calculated', 'Calculated from spatial data');
INSERT INTO metric_sources (fid, name,  description) VALUES (2, 'Estimated', 'Estimated from other sources or evidence');


-- fundamental question is about geometry
CREATE TABLE  layers (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    fc_name TEXT UNIQUE NOT NULL,
    display_name TEXT UNIQUE NOT NULL,
    qml TEXT NOT NULL,
    geom_type TEXT,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (1, 'dam_crests', 'Dam Crests', 'Linestring', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (3, 'dams', 'Dam Points', 'Point', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (4, 'jams', 'Jam Points', 'Point', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (5, 'thalwegs', 'Thalwegs', 'Linestring', 'temp.qml', NULL); -- type: primary, secondary - see GUT
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (6, 'riverscape_units', 'Riverscape Units', 'Polygon', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (7, 'centerlines', 'Centerlines', 'Linestring', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (8, 'inundation_extents', 'Inundation Extents', 'Polygon', 'temp.qml', NULL); -- type: free flow, overflow, ponded
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (9, 'valley_bottoms', 'Valley Bottoms', 'Polygon', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (10, 'junctions', 'Junctions', 'Point', 'temp.qml', NULL); -- type: convergence, divergence
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (11, 'geomorphic_unit_extents', 'Geomorphic Unit Extents', 'Polygon', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (12, 'geomorphic_units', 'Geomorphic Unit Points', 'Point', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (13, 'geomorphic_units_tier3', 'Tier 3 Geomorphic Units', 'Point', 'temp.qml', NULL); -- fluvial taxonomy
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (14, 'cem_phases', 'Channel Evolution Model Stages', 'Polygon', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (15, 'vegetation_extents', 'Vegetation Extents', 'Polygon', 'temp.qml', NULL); -- veg_classes
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (16, 'floodplain_accessibilities', 'Floodplain Accessibility', 'Polygon', 'temp.qml', NULL); -- floating point accessibility
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (17, 'zoi_extent', 'Zones of Influence', 'Polygon', 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, qml, description) VALUES (18, 'brat_vegetation', 'Brat Vegetation Suitability', 'Polygon', 'temp.qml', NULL);


CREATE TABLE  method_layers (
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    layer_id INTEGER REFERENCES layers(fid) ON DELETE CASCADE,
    CONSTRAINT pk_method_layers PRIMARY KEY (method_id, layer_id)
);


INSERT INTO method_layers (method_id, layer_id) VALUES (1, 1);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 5);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 8);
INSERT INTO method_layers (method_id, layer_id) VALUES (2, 6);
INSERT INTO method_layers (method_id, layer_id) VALUES (2, 9);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 3);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 4);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 12);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 11);


-- NON-SPATIAL TABLES
CREATE TABLE projects (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_by TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE assessments (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(fid) ON DELETE CASCADE,
    epoch TEXT,
    description TEXT,
    start_date DATE,
    end_date DATE,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE platform (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessment_methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES platform(fid) ON DELETE CASCADE,
    description TEXT,
    date DATE,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE bases (
    -- this table name is horid. try: contexts, evidences, base_rasters
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(fid) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    path TEXT UNIQUE NOT NULL,
    -- type will likely be populated from a lookup. e.g., imagery, dem, lidar, etc....
    type TEXT,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessment_bases (
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    base_id INTEGER REFERENCES bases(fid) ON DELETE CASCADE
);

CREATE TABLE mask_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO mask_types (fid, name) VALUES (1, 'Regular Mask');
INSERT INTO mask_types (fid, name) VALUES (2, 'Directional Mask');
INSERT INTO mask_types (fid, name) VALUES (3, 'Area of Interest (AOI)');

------------------------------
CREATE TABLE masks (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(fid) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    mask_type_id INTEGER NOT NULL REFERENCES masks(fid),
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE mask_features ADD COLUMN mask_id INTEGER REFERENCES masks(fid) ON DELETE CASCADE;
ALTER TABLE mask_features ADD COLUMN name TEXT;
ALTER TABLE mask_features ADD COLUMN position INTEGER;
ALTER TABLE mask_features ADD COLUMN description TEXT;


CREATE TABLE calculations (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE metrics (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculations(fid) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE metric_values (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    mask_feature_id INTEGER REFERENCES mask_features(fid) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES metrics(fid) ON DELETE CASCADE,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    metric_source_id INTEGER REFERENCES metric_sources(fid) ON DELETE CASCADE,
    value NUMERIC,
    Uncertainty NUMERIC,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- dam and jam surveys
CREATE TABLE structure_source (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO structure_source (fid, name) VALUES (1, 'Natural');
INSERT INTO structure_source (fid, name) VALUES (2, 'Artificial');
INSERT INTO structure_source (fid, name) VALUES (3, 'Unknown');


CREATE TABLE dam_integrity (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO dam_integrity (fid, name) VALUES (1, 'Intact');
INSERT INTO dam_integrity (fid, name) VALUES (2, 'Breached');
INSERT INTO dam_integrity (fid, name) VALUES (3, 'Blown');
INSERT INTO dam_integrity (fid, name) VALUES (4, 'Burried');
INSERT INTO dam_integrity (fid, name) VALUES (5, 'Flooded');
INSERT INTO dam_integrity (fid, name) VALUES (6, 'NA');

------------------------------------------------------
CREATE TABLE beaver_maintenance (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO beaver_maintenance (fid, name) VALUES (1, 'None');
INSERT INTO beaver_maintenance (fid, name) VALUES (2, 'Old');
INSERT INTO beaver_maintenance (fid, name) VALUES (3, 'Fresh');
INSERT INTO beaver_maintenance (fid, name) VALUES (4, 'NA');


-- dam crests
ALTER TABLE dam_crests ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN structure_source_id INTEGER REFERENCES structure_source(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN dam_integrity_id INTEGER REFERENCES dam_integrity(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN beaver_maintenance_id INTEGER REFERENCES beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN height NUMERIC;

-- dam points
ALTER TABLE dams ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN structure_source_id INTEGER REFERENCES structure_source(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN dam_integrity_id INTEGER REFERENCES dam_integrity(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN length NUMERIC;
ALTER TABLE dams ADD COLUMN height NUMERIC;

-- jam points
ALTER TABLE jams ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN structure_source_id INTEGER REFERENCES structure_source(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN length NUMERIC;
ALTER TABLE jams ADD COLUMN width NUMERIC;
ALTER TABLE jams ADD COLUMN height NUMERIC;
ALTER TABLE jams ADD COLUMN wood_count INTEGER;

-- thalwegs
CREATE TABLE thalweg_types(
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO thalweg_types (fid, name) VALUES (1, 'Primary');
INSERT INTO thalweg_types (fid, name) VALUES (2, 'Non-Primary');


ALTER TABLE thalwegs ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE thalwegs ADD COLUMN type_id INTEGER REFERENCES thalweg_types(fid) ON DELETE CASCADE;


----------------------------------
-- riverscape units
CREATE TABLE riverscape_unit_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO riverscape_unit_types (fid, name) VALUES (1, 'Active');
INSERT INTO riverscape_unit_types (fid, name) VALUES (2, 'Inactive');

ALTER TABLE riverscape_units ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE riverscape_units ADD COLUMN type_id INTEGER REFERENCES riverscape_unit_types(fid) ON DELETE CASCADE;

-- centerlines
ALTER TABLE centerlines ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;

-- inundation
ALTER TABLE inundation_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;

-- valley bottoms
ALTER TABLE valley_bottoms ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE  CASCADE;


-- junctions
CREATE TABLE junction_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO junction_types (fid, name) VALUES (1, 'Confluence');
INSERT INTO junction_types (fid, name) VALUES (2, 'Diffluence');


ALTER TABLE junctions ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE junctions ADD COLUMN type_id INTEGER REFERENCES junction_types(fid) ON DELETE CASCADE;


-- geomorphic units
CREATE TABLE geomorphic_unit_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO geomorphic_unit_types (fid, name) VALUES (1, 'Concavity');
INSERT INTO geomorphic_unit_types (fid, name) VALUES (2, 'Convexity');
INSERT INTO geomorphic_unit_types (fid, name) VALUES (3, 'Planner');


ALTER TABLE geomorphic_units ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE geomorphic_units ADD COLUMN type_id INTEGER REFERENCES geomorphic_unit_types(fid) ON DELETE CASCADE;


ALTER TABLE geomorphic_unit_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE geomorphic_unit_extents ADD COLUMN type_id INTEGER REFERENCES geomorphic_unit_types(fid) ON DELETE CASCADE;

---------------------------------------------------------
-- cem phases
CREATE TABLE cem_phase_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO cem_phase_types (fid, name) VALUES (1, 'Stage-1');
INSERT INTO cem_phase_types (fid, name) VALUES (2, 'Stage-5');
INSERT INTO cem_phase_types (fid, name) VALUES (3, 'Stage-0');


ALTER TABLE cem_phases ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE cem_phases ADD COLUMN type_id INTEGER REFERENCES cem_phase_types(fid) ON DELETE CASCADE;

-- vegetation extents
CREATE TABLE vegetation_extent_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO vegetation_extent_types (fid, name) VALUES (1, 'Riparian');
INSERT INTO vegetation_extent_types (fid, name) VALUES (2, 'Wetland');
INSERT INTO vegetation_extent_types (fid, name) VALUES (3, 'Upland');
INSERT INTO vegetation_extent_types (fid, name) VALUES (4, 'Other');

ALTER TABLE vegetation_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE vegetation_extents ADD COLUMN type_id INTEGER REFERENCES vegetation_extent_types(fid) ON DELETE CASCADE;

-- floodplain acessibility
CREATE TABLE floodplain_accessibility_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO floodplain_accessibility_types (fid, name) VALUES (1, 'Inaccessible');
INSERT INTO floodplain_accessibility_types (fid, name) VALUES (2, 'Surface water Accessible');
INSERT INTO floodplain_accessibility_types (fid, name) VALUES (3, 'Groundwater Accessible');
INSERT INTO floodplain_accessibility_types (fid, name) VALUES (4, 'Fully Accessible');


ALTER TABLE floodplain_accessibilities ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE floodplain_accessibilities ADD COLUMN type_id INTEGER REFERENCES floodplain_accessibility_types(fid) ON DELETE CASCADE;

-- zoi_extents
ALTER TABLE zoi_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;

-- brat vegetation
CREATE TABLE brat_vegetation_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO brat_vegetation_types (fid, name) VALUES (1, 'Preferred');
INSERT INTO brat_vegetation_types (fid, name) VALUES (2, 'Suitable');
INSERT INTO brat_vegetation_types (fid, name) VALUES (3, 'Moderately Suitable');
INSERT INTO brat_vegetation_types (fid, name) VALUES (4, 'Barely Suitable');
INSERT INTO brat_vegetation_types (fid, name) VALUES (5, 'Unsuitable');


ALTER TABLE brat_vegetation ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE brat_vegetation ADD COLUMN type_id INTEGER REFERENCES brat_vegetation_types(fid) ON DELETE CASCADE;



-- add to geopackage contents
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_structure_mimics", "attributes", "lkp_structure_mimics", 0);




