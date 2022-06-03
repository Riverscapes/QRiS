-- Database migrations tracking
CREATE TABLE migrations (
  migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT UNIQUE NOT NULL,
  created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- LOOKUP TABLES
CREATE TABLE  methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- major question is whether a method is specific to the type of geometry used?
-- methods could also be specific to whether the survey is being conducted in the field or on the desktop.
INSERT INTO methods (fid, name, description) VALUES (1, 'RIM', 'Riverscape Inundation Mapping');
INSERT INTO methods (fid, name, description) VALUES (2, 'Riverscape Units', 'Placeholder name for the streams need space stupidity');
INSERT INTO methods (fid, name, description) VALUES (3, 'Low-Tech Design', 'Documentation of a design or as-built low-tech structures');
INSERT INTO methods (fid, name, description) VALUES (4, 'Structural Elements', 'Survey of primary structural element types');
INSERT INTO methods (fid, name, description) VALUES (5, 'Geomorphic Units', 'Some sort of riverscape feature classification, who fricken knows');
INSERT INTO methods (fid, name, description) VALUES (6, 'Channel Units', 'Simplified channel unit survey for in-channel features. Compliments Low-Tech. Monitoring Protocol');


CREATE TABLE  lkp_metric_sources (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_metric_sources (fid, name,  description) VALUES (1, 'Calculated', 'Calculated from spatial data');
INSERT INTO lkp_metric_sources (fid, name,  description) VALUES (2, 'Estimated', 'Estimated from other sources or evidence');


CREATE TABLE  layers (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    fc_name TEXT UNIQUE NOT NULL,
    display_name TEXT UNIQUE NOT NULL,
    qml TEXT NOT NULL,
    is_lookup BOOLEAN,
    geom_type TEXT,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Layers
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (1, 'dam_crests', 'Dam Crests', 'Linestring', 0, 'dam_crests.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (3, 'dams', 'Dam Points', 'Point', 0, 'dams.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (4, 'jams', 'Jam Points', 'Point', 0, 'jams.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (5, 'thalwegs', 'Thalwegs', 'Linestring', 0, 'thalwegs.qml', NULL); -- type: primary, secondary - see GUT
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (6, 'riverscape_units', 'Riverscape Units', 'Polygon', 0, 'riverscape_units.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (7, 'centerlines', 'Centerlines', 'Linestring', 0, 'centerlines.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (8, 'inundation_extents', 'Inundation Extents', 'Polygon', 0, 'inundation_extents.qml', NULL); -- type: free flow, overflow, ponded
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (9, 'valley_bottoms', 'Valley Bottoms', 'Polygon', 0, 'valley_bottoms.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (10, 'junctions', 'Junctions', 'Point', 0, 'junctions.qml', NULL); -- type: convergence, divergence
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (11, 'geomorphic_unit_extents', 'Geomorphic Unit Extents', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (12, 'geomorphic_units', 'Geomorphic Unit Points', 'Point', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (13, 'geomorphic_units_tier3', 'Tier 3 Geomorphic Units', 'Point', 0, 'temp.qml', NULL); -- fluvial taxonomy
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (14, 'cem_phases', 'Channel Evolution Model Stages', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (15, 'vegetation_extents', 'Vegetation Extents', 'Polygon', 0, 'temp.qml', NULL); -- veg_classes
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (16, 'floodplain_accessibilities', 'Floodplain Accessibility', 'Polygon', 0, 'temp.qml', NULL); -- floating point accessibility
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (17, 'brat_vegetation', 'Brat Vegetation Suitability', 'Polygon', 0, 'temp.qml', NULL);
-- INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (18, 'designs', 'Design', 'NoGeometry', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (19, 'zoi', 'Zones of influence', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (20, 'complexes', 'Structure Complex Extents', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (21, 'structure_points', 'Structure Points', 'Point', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (22, 'structure_lines', 'Structure Lines', 'Linestring', 0, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (23, 'channel_unit_points', 'Channel Unit Points', 'Point', 0, 'channel_unit_points.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (24, 'channel_unit_polygons', 'Channel Unit Polygons ', 'Polygon', 0, 'channel_unit_polygons.qml', NULL);

-- Lookup Tables
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (100, 'lkp_metric_sources', 'Metric Sources', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (101, 'lkp_platform', 'Platform', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (102, 'lkp_mask_types', 'Mask Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (103, 'lkp_structure_source', 'Structure Sources', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (104, 'lkp_dam_integrity', 'Dam Integrity', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (105, 'lkp_beaver_maintenance', 'Beaver Maintenance', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (106, 'lkp_thalweg_types', 'Thalweg Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (107, 'lkp_riverscape_unit_types', 'Riverscape Units Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (108, 'lkp_junction_types', 'Junction Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (109, 'lkp_geomorphic_unit_types', 'Geomorphic Unit Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (110, 'lkp_vegetation_extent_types', 'Vegetation Extent Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (111, 'lkp_cem_phase_types', 'CEM Phase Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (112, 'lkp_floodplain_accessibility_types', 'Floodplain Accessibility Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (113, 'lkp_brat_vegetation_types', 'Brat Vegetation Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (114, 'lkp_context_layer_types', 'Context Layer Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (115, 'lkp_inundation_extent_types', 'Inundation Extent Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (116, 'lkp_primary_channel', 'Primary Channel Type', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (117, 'lkp_primary_unit', 'Primary Unit Type', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (118, 'lkp_structure_forced', 'Structure Forced', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (119, 'lkp_channel_unit_types', 'Channel Unit Types', 'NoGeometry', 1, 'temp.qml', NULL);

INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (120, 'lkp_design_status', 'Design Status', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (121, 'lkp_structure_mimics', 'Structure Mimics', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (122, 'lkp_zoi_stage', 'ZOI Stage', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (123, 'structure_types', 'Structure Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (fid, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (124, 'zoi_types', 'Zoi Types', 'NoGeometry', 1, 'temp.qml', NULL);


CREATE TABLE  method_layers (
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    layer_id INTEGER REFERENCES layers(fid) ON DELETE CASCADE,
    metadata TEXT,
    CONSTRAINT pk_method_layers PRIMARY KEY (method_id, layer_id)
);

-- RIM
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 1);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 5);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 8);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 106);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 115);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 103);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 105); 
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 104);
-- Structural Elements
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 3);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 4);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 1);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 103);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 104);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 105);
-- Low Tech Designs
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 19);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 20);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 21);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 22);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 120);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 121);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 122);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 123);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 124);
-- Channel Units
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 22);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 23);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 116);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 117);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 118);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 119);



CREATE TABLE lkp_context_layer_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_context_layer_types (fid, name) VALUES (1, 'Aerial imagery');
INSERT INTO lkp_context_layer_types (fid, name) VALUES (2, 'DEM');
INSERT INTO lkp_context_layer_types (fid, name) VALUES (3, 'Detrended DEM');
INSERT INTO lkp_context_layer_types (fid, name) VALUES (4, 'Hillshade');
INSERT INTO lkp_context_layer_types (fid, name) VALUES (5, 'Other');

-- so, can these be vector and raster? does it matter?
CREATE TABLE context_layers (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER REFERENCES lkp_context_layer_types(fid) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    path TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE projects (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_by TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE assessments (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    epoch TEXT,
    description TEXT,
    metadata TEXT,
    start_date DATE,
    end_date DATE,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lkp_platform (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessment_methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES lkp_platform(fid) ON DELETE CASCADE,
    description TEXT,
    metadata TEXT,
    date DATE,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE basemaps (
    -- this table name is horid. try: contexts, evidences, base_rasters
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT UNIQUE NOT NULL,
    -- type will likely be populated from a lookup. e.g., imagery, dem, lidar, etc....
    type TEXT,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessment_basemaps (
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    basemap_id INTEGER REFERENCES bases(fid) ON DELETE CASCADE
);

CREATE TABLE lkp_mask_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- need to review these types. I'm not totally sure that this is necessary in a table.
INSERT INTO lkp_mask_types (fid, name) VALUES (1, 'Regular Mask');
INSERT INTO lkp_mask_types (fid, name) VALUES (2, 'Directional Mask');
INSERT INTO lkp_mask_types (fid, name) VALUES (3, 'Area of Interest (AOI)');

CREATE TABLE masks (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    mask_type_id INTEGER NOT NULL REFERENCES masks(fid),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE mask_features ADD COLUMN mask_id INTEGER REFERENCES masks(fid) ON DELETE CASCADE;
-- ALTER TABLE mask_features ADD COLUMN name TEXT;
ALTER TABLE mask_features ADD COLUMN position INTEGER;
ALTER TABLE mask_features ADD COLUMN description TEXT;
ALTER TABLE mask_features ADD COLUMN metadata TEXT;


CREATE TABLE calculations (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE metrics (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculations(fid) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE metric_values (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    mask_feature_id INTEGER REFERENCES mask_features(fid) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES metrics(fid) ON DELETE CASCADE,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
--     metric_source_id INTEGER REFERENCES metric_sources(fid) ON DELETE CASCADE,
    value NUMERIC,
    metadata TEXT,
    Uncertainty NUMERIC,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- dam and jam surveys
CREATE TABLE lkp_structure_source (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_source (fid, name) VALUES (1, 'Natural');
INSERT INTO lkp_structure_source (fid, name) VALUES (2, 'Artificial');
INSERT INTO lkp_structure_source (fid, name) VALUES (3, 'Unknown');


CREATE TABLE lkp_dam_integrity (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_dam_integrity (fid, name) VALUES (1, 'Intact');
INSERT INTO lkp_dam_integrity (fid, name) VALUES (3, 'Blown');
INSERT INTO lkp_dam_integrity (fid, name) VALUES (2, 'Breached');
INSERT INTO lkp_dam_integrity (fid, name) VALUES (4, 'Burried');
INSERT INTO lkp_dam_integrity (fid, name) VALUES (5, 'Flooded');
INSERT INTO lkp_dam_integrity (fid, name) VALUES (6, 'NA');

CREATE TABLE lkp_beaver_maintenance (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_beaver_maintenance (fid, name) VALUES (1, 'None');
INSERT INTO lkp_beaver_maintenance (fid, name) VALUES (2, 'Old');
INSERT INTO lkp_beaver_maintenance (fid, name) VALUES (3, 'Fresh');
INSERT INTO lkp_beaver_maintenance (fid, name) VALUES (4, 'NA');


-- dam crests
ALTER TABLE dam_crests ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN dam_integrity_id INTEGER REFERENCES lkp_dam_integrity(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN height NUMERIC;

-- dam points
ALTER TABLE dams ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN dam_integrity_id INTEGER REFERENCES lkp_dam_integrity(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN length NUMERIC;
ALTER TABLE dams ADD COLUMN height NUMERIC;

-- jam points
ALTER TABLE jams ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(fid) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN length NUMERIC;
ALTER TABLE jams ADD COLUMN width NUMERIC;
ALTER TABLE jams ADD COLUMN height NUMERIC;
ALTER TABLE jams ADD COLUMN wood_count INTEGER;

-- thalwegs
CREATE TABLE lkp_thalweg_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_thalweg_types (fid, name) VALUES (1, 'Primary');
INSERT INTO lkp_thalweg_types (fid, name) VALUES (2, 'Non-Primary');


ALTER TABLE thalwegs ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE thalwegs ADD COLUMN type_id INTEGER REFERENCES lkp_thalweg_types(fid) ON DELETE CASCADE;


-- riverscape units
CREATE TABLE lkp_riverscape_unit_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_riverscape_unit_types (fid, name) VALUES (1, 'Active');
INSERT INTO lkp_riverscape_unit_types (fid, name) VALUES (2, 'Inactive');

ALTER TABLE riverscape_units ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE riverscape_units ADD COLUMN type_id INTEGER REFERENCES lkp_riverscape_unit_types(fid) ON DELETE CASCADE;

-- centerlines
ALTER TABLE centerlines ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;

CREATE TABLE lkp_inundation_extent_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_inundation_extent_types (fid, name) VALUES (1, 'Free Flowing');
INSERT INTO lkp_inundation_extent_types (fid, name) VALUES (2, 'Ponded');
INSERT INTO lkp_inundation_extent_types (fid, name) VALUES (3, 'Overflow');


-- inundation
ALTER TABLE inundation_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE inundation_extents ADD COLUMN type_id INTEGER REFERENCES lkp_inundation_extent_types(fid) ON DELETE CASCADE;

-- valley bottoms
ALTER TABLE valley_bottoms ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE  CASCADE;


-- junctions
CREATE TABLE lkp_junction_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_junction_types (fid, name) VALUES (1, 'Confluence');
INSERT INTO lkp_junction_types (fid, name) VALUES (2, 'Diffluence');


ALTER TABLE junctions ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE junctions ADD COLUMN type_id INTEGER REFERENCES lkp_junction_types(fid) ON DELETE CASCADE;


-- geomorphic units
CREATE TABLE lkp_geomorphic_unit_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_geomorphic_unit_types (fid, name) VALUES (1, 'Concavity');
INSERT INTO lkp_geomorphic_unit_types (fid, name) VALUES (2, 'Convexity');
INSERT INTO lkp_geomorphic_unit_types (fid, name) VALUES (3, 'Planner');
INSERT INTO lkp_geomorphic_unit_types (fid, name) VALUES (4, 'Pond');

ALTER TABLE geomorphic_units ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE geomorphic_units ADD COLUMN type_id INTEGER REFERENCES lkp_geomorphic_unit_types(fid) ON DELETE CASCADE;


ALTER TABLE geomorphic_unit_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE geomorphic_unit_extents ADD COLUMN type_id INTEGER REFERENCES lkp_geomorphic_unit_types(fid) ON DELETE CASCADE;

-- cem phases
CREATE TABLE lkp_cem_phase_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_cem_phase_types (fid, name) VALUES (1, 'Stage-1');
INSERT INTO lkp_cem_phase_types (fid, name) VALUES (2, 'Stage-5');
INSERT INTO lkp_cem_phase_types (fid, name) VALUES (3, 'Stage-0');


ALTER TABLE cem_phases ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE cem_phases ADD COLUMN type_id INTEGER REFERENCES lkp_cem_phase_types(fid) ON DELETE CASCADE;

-- vegetation extents
CREATE TABLE lkp_vegetation_extent_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_vegetation_extent_types (fid, name) VALUES (1, 'Riparian');
INSERT INTO lkp_vegetation_extent_types (fid, name) VALUES (2, 'Wetland');
INSERT INTO lkp_vegetation_extent_types (fid, name) VALUES (3, 'Upland');
INSERT INTO lkp_vegetation_extent_types (fid, name) VALUES (4, 'Other');

ALTER TABLE vegetation_extents ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE vegetation_extents ADD COLUMN type_id INTEGER REFERENCES lkp_vegetation_extent_types(fid) ON DELETE CASCADE;

-- floodplain acessibility
CREATE TABLE lkp_floodplain_accessibility_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_floodplain_accessibility_types (fid, name) VALUES (1, 'Inaccessible');
INSERT INTO lkp_floodplain_accessibility_types (fid, name) VALUES (2, 'Surface water Accessible');
INSERT INTO lkp_floodplain_accessibility_types (fid, name) VALUES (3, 'Groundwater Accessible');
INSERT INTO lkp_floodplain_accessibility_types (fid, name) VALUES (4, 'Fully Accessible');


ALTER TABLE floodplain_accessibilities ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE floodplain_accessibilities ADD COLUMN type_id INTEGER REFERENCES lkp_floodplain_accessibility_types(fid) ON DELETE CASCADE;


-- brat vegetation
CREATE TABLE lkp_brat_vegetation_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_vegetation_types (fid, name) VALUES (1, 'Preferred');
INSERT INTO lkp_brat_vegetation_types (fid, name) VALUES (2, 'Suitable');
INSERT INTO lkp_brat_vegetation_types (fid, name) VALUES (3, 'Moderately Suitable');
INSERT INTO lkp_brat_vegetation_types (fid, name) VALUES (4, 'Barely Suitable');
INSERT INTO lkp_brat_vegetation_types (fid, name) VALUES (5, 'Unsuitable');


ALTER TABLE brat_vegetation ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE brat_vegetation ADD COLUMN type_id INTEGER REFERENCES lkp_brat_vegetation_types(fid) ON DELETE CASCADE;


-- channel unit layers
CREATE TABLE lkp_channel_unit_types (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_channel_unit_types (fid, name) VALUES (1, 'Concavity');
INSERT INTO lkp_channel_unit_types (fid, name) VALUES (2, 'Convexity');
INSERT INTO lkp_channel_unit_types (fid, name) VALUES (3, 'Planar');
INSERT INTO lkp_channel_unit_types (fid, name) VALUES (4, 'Pond');
INSERT INTO lkp_channel_unit_types (fid, name) VALUES (5, 'NA');


CREATE TABLE lkp_structure_forced (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_forced (fid, name) VALUES (1, 'Artificial Structure');
INSERT INTO lkp_structure_forced (fid, name) VALUES (2, 'Natural Structure');
INSERT INTO lkp_structure_forced (fid, name) VALUES (3, 'Not Structure Forced');
INSERT INTO lkp_structure_forced (fid, name) VALUES (4, 'NA');


CREATE TABLE lkp_primary_channel (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_primary_channel (fid, name) VALUES (1, 'Primary Channel');
INSERT INTO lkp_primary_channel (fid, name) VALUES (2, 'Non-Primary Channel');
INSERT INTO lkp_primary_channel (fid, name) VALUES (3, 'NA');

CREATE TABLE lkp_primary_unit (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_primary_unit (fid, name) VALUES (1, 'Primary Unit');
INSERT INTO lkp_primary_unit (fid, name) VALUES (2, 'Non-Primary Unit');
INSERT INTO lkp_primary_unit (fid, name) VALUES (3, 'NA');


ALTER TABLE channel_unit_points ADD COLUMN description TEXT;
ALTER TABLE channel_unit_points ADD COLUMN unit_type_id INTEGER REFERENCES lkp_channel_unit_types(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN structure_forced_id INTEGER REFERENCES lkp_structure_forced(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN primary_unit_id INTEGER REFERENCES lkp_primary_unit(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN primary_channel_id INTEGER REFERENCES lkp_primary_channel(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN length NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN width NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN depth NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN percent_wetted NUMERIC;

ALTER TABLE channel_unit_polygons ADD COLUMN description TEXT;
ALTER TABLE channel_unit_polygons ADD COLUMN unit_type_id INTEGER REFERENCES lkp_channel_unit_types(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN structure_forced_id INTEGER REFERENCES lkp_structure_forced(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN primary_unit_id INTEGER REFERENCES lkp_primary_unit(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN primary_channel_id INTEGER REFERENCES lkp_primary_channel(fid) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN percent_wetted NUMERIC;


-- Design Lookup Tables
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

INSERT INTO zoi_types (fid, name, description) VALUES (1, "Increase Channel Complexity", "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment");
INSERT INTO zoi_types (fid, name, description) VALUES (2, "Accelerate Incision Recovery", "Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation");
INSERT INTO zoi_types (fid, name, description) VALUES (3, "Lateral Channel Migration", "Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders");
INSERT INTO zoi_types (fid, name, description) VALUES (4, "Increase Floodplain Connectivity", "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow");
INSERT INTO zoi_types (fid, name, description) VALUES (5, "Facilitate Beaver Translocation", "Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation");
INSERT INTO zoi_types (fid, name, description) VALUES (6, "Other", "Area of hydraulic feature creation (e.g., eddy, shear zone, hydraulic jet)");



-- Design Spatial Table Fields and Relationships
ALTER TABLE zoi ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN type_id INTEGER REFERENCES zoi_types(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN stage_id INTEGER REFERENCES lkp_zoi_stage(fid) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN description TEXT;
ALTER TABLE zoi ADD COLUMN created DATETIME;


ALTER TABLE complexes ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE complexes ADD COLUMN description TEXT;
ALTER TABLE complexes ADD COLUMN initial_condition TEXT;
ALTER TABLE complexes ADD COLUMN target_condition TEXT;
ALTER TABLE complexes ADD COLUMN created DATETIME;


ALTER TABLE structure_lines ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN name TEXT;
ALTER TABLE structure_lines ADD COLUMN description TEXT;
ALTER TABLE structure_lines ADD COLUMN created DATETIME;


ALTER TABLE structure_points ADD COLUMN assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(fid) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN name TEXT;
ALTER TABLE structure_points ADD COLUMN description TEXT;
ALTER TABLE structure_points ADD COLUMN created DATETIME;


-- add to geopackage contents
-- this is only necessary for non-spatial tables created using ddl.
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('methods', 'attributes', 'methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('layers', 'attributes', 'layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('context_layers', 'attributes', 'context_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('method_layers', 'attributes', 'method_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('projects', 'attributes', 'projects', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('assessments', 'attributes', 'assessments', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('assessment_methods', 'attributes', 'assessment_methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('bases', 'attributes', 'bases', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('assessment_bases', 'attributes', 'assessment_bases', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('masks', 'attributes', 'masks', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('calculations', 'attributes', 'calculations', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metrics', 'attributes', 'metrics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metric_values', 'attributes', 'metric_values', 0);

-- LOOKUP TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_metric_sources', 'attributes', 'lkp_metric_sources', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_platform', 'attributes', 'lkp_platform', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_mask_types', 'attributes', 'lkp_mask_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_source', 'attributes', 'lkp_structure_source', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_dam_integrity', 'attributes', 'lkp_dam_integrity', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_beaver_maintenance', 'attributes', 'lkp_beaver_maintenance', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_thalweg_types', 'attributes', 'lkp_thalweg_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_riverscape_unit_types', 'attributes', 'lkp_riverscape_unit_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_junction_types', 'attributes', 'lkp_junction_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_geomorphic_unit_types', 'attributes', 'lkp_geomorphic_unit_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_vegetation_extent_types', 'attributes', 'lkp_vegetation_extent_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_cem_phase_types', 'attributes', 'lkp_cem_phase_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_floodplain_accessibility_types', 'attributes', 'lkp_floodplain_accessibility_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_vegetation_types', 'attributes', 'lkp_brat_vegetation_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_context_layer_types', 'attributes', 'lkp_context_layer_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_inundation_extent_types', 'attributes', 'lkp_inundation_extent_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_channel', 'attributes', 'lkp_primary_channel', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_unit', 'attributes', 'lkp_primary_unit', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_forced', 'attributes', 'lkp_structure_forced', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_channel_unit_types', 'attributes', 'lkp_channel_unit_types', 0);

-- DESIGN TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_structure_mimics", "attributes", "lkp_structure_mimics", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_zoi_stage", "attributes", "lkp_zoi_stage", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("lkp_design_status", "attributes", "lkp_design_status", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structure_types", "attributes", "structure_types", 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("zoi_types", "attributes", "zoi_types", 0);
