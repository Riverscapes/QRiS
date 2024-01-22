-- Database migrations tracking
CREATE TABLE migrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT UNIQUE NOT NULL,
  created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- INSERT INTO migrations (file_name) VALUES ('001_initial_schema.sql');


-- LOOKUP TABLES
CREATE TABLE protocols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    machine_code TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    has_custom_ui BOOLEAN,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (1, 'LTPBR BASE', 'LTPBR_BASE', 0, 'Base LTPBR Layers');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (4, 'Low-Tech Design', 'DESIGN', 1, 'Documentation of a design or as-built low-tech structures');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (5, 'As-Built', 'ASBUILT', 1, 'Documentation of as-built low-tech structures'); 

CREATE TABLE methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    machine_code TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO methods (id, name, machine_code) VALUES (1, 'Methods', 'METHODS');
INSERT INTO methods (id, name, machine_code) VALUES (5, 'LT-PBR Design', 'LTPBRDESIGN');
INSERT INTO methods (id, name, machine_code) VALUES (6, 'LT-PBR As-Built', 'LTPBRASBUILT');

CREATE TABLE protocol_methods (
    protocol_id INTEGER NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
    method_id INTEGER NOT NULL REFERENCES methods(id) ON DELETE CASCADE,

    CONSTRAINT pk_protocol_methods PRIMARY KEY (protocol_id, method_id)
);

INSERT INTO protocol_methods (protocol_id, method_id) VALUES (1, 1);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (4, 5);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (5, 6);


CREATE TABLE layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fc_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    qml TEXT NOT NULL,
    is_lookup BOOLEAN,
    geom_type TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Layers
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (1, 'dam_crests', 'Dam Crests', 'Linestring', 0, 'dam_crests.qml', NULL, '{"hierarchy": ["Assessments", "Beaver Dam Building"], "fields": [{"machine_code": "structure_source_id", "label": "Structure Source", "type": "list", "lookup": "structure_source"}, {"machine_code": "dam_integrity_id", "label": "Dam Integrity", "type": "list", "lookup": "dam_integrity"}, {"machine_code": "beaver_maintenance_id", "label": "Beaver Maintenance", "type": "list" ,"lookup": "beaver_maintenance"}]}');
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (2, 'jam_area', 'Jam Areas', 'Polygon', 0, 'jam_area.qml', NULL, '{"fields": [{"machine_code": "structure_source_id", "label": "Structure Source", "type": "list", "lookup": "structure_source"}, {"machine_code": "beaver_maintenance_id", "label": "Beaver Maintenance", "type": "list", "lookup": "beaver_maintenance"}]}');
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (3, 'dams', 'Dam Points', 'Point', 0, 'dams.qml', NULL, '{"fields": [{"machine_code": "structure_source_id", "label": "Structure Source", "type": "list", "lookup": "structure_source"}, {"machine_code": "dam_integrity_id", "label": "Dam Integrity", "type": "list", "lookup": "dam_integrity"}, {"machine_code": "beaver_maintenance_id", "label": "Beaver Maintenance", "type": "list", "lookup": "lkp_beaver_maintenance"}]}');
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (4, 'jams', 'Jam Points', 'Point', 0, 'jams.qml', NULL, '{"fields": [{"machine_code": "structure_source_id", "label": "Structure Source", "type": "list", "lookup": "structure_source"}, {"machine_code": "beaver_maintenance_id", "label": "Beaver Maintenance", "type": "list", "lookup": "beaver_maintenance"}]}');

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (5, 'active_channel', 'Active Channel(s) (bankfull)', 'Polygon', 0, 'active_channels.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (6, 'active_extents', 'Active Extents', 'Polygon', 0, 'active_extents.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Floodplain"], "fields": [{"machine_code": "type_id", "label": "Type", "type": "list", "lookup": "active_extent_types"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (7, 'centerlines', 'Centerline(s) of Active Channel(s)', 'Linestring', 0, 'centerlines.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "type_id", "label": "Type", "type": "list", "lookup": "centerline_types"}, {"machine_code": "description", "label": "Description", "type": "list", "lookup": "centerline_descriptions", "default": "Centerline"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (8, 'inundation_extents', 'Inundation', 'Polygon', 0, 'inundation_extents.qml', NULL, '{"hierarchy": ["Observations", "Hydraulic Mapping"], "fields": [{"machine_code": "type_id", "label": "Extent Type", "type": "list", "lookup": "inundation_extent_types"}]}'); -- type: free flow, overflow, ponded
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (10, 'channel_junctions', 'Channel Junctions', 'Point', 0, 'channel_junctions.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "junction_type", "label": "Type", "type": "list", "lookup": "junction_types"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (11, 'geomorphic_unit_extents', 'Geomorphic Units', 'Polygon', 0, 'geomorphic_unit_extents.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "geomorphic_unit_type_2_tier", "label": "Type 2 Tier", "type": "list", "lookup": "geomorphic_units_tier2_types"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (12, 'geomorphic_units', 'Geomorphic Unit Points', 'Point', 0, 'geomorphic_units.qml', NULL, '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "geomorphic_unit_type_2_tier", "label": "Type 2 Tier", "type": "list", "lookup": "geomorphic_units_tier2_types"}, {"machine_code": "length", "label": "Length", "type": "float"}, {"machine_code": "width", "label": "Width", "type": "float"}, {"machine_code": "depth", "label": "Depth", "type": "float"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (14, 'cem_phases', 'CEM', 'Polygon', 0, 'cem_phases.qml', NULL, '{"hierarchy": ["Assessments", "Geomorphic Condition"], "fields": [{"machine_code": "cem_stage", "label": "CEM Stage", "type": "integer", "max": 8}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (15, 'vegetation_extents', 'Vegetation Extents', 'Polygon', 0, 'vegetation_extents.qml', NULL, '{"hierarchy": ["Observations", "Vegetation Mapping"]}');

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (17, 'brat_vegetation', 'Brat Vegetation Suitability', 'Polygon', 0, 'brat_vegetation.qml', NULL, '{"hierarchy": ["Assessments", "Beaver Dam Building"], "fields": [{"machine_code": "vegetation_suitability", "label": "Suitability", "type": "integer"}]}');

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (19, 'zoi', 'Zones of Influence', 'Polygon', 0, 'zoi.qml', NULL, '{"fields": [{"machine_code": "zoi_type", "label": "ZOI Type", "type": "list", "lookup": "zoi_types"}, {"machine_code": "zoi_stage", "label": "ZOI Stage", "type": "list", "lookup": "zoi_stages"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (20, 'complexes', 'Structure Complex Extents', 'Polygon', 0, 'complexes.qml', NULL, '{"hierarchy": ["Structures"], "fields": []}'); --NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (21, 'structure_points', 'Structure Points', 'Point', 0, 'structure_points.qml', NULL, '{"hierarchy": ["Structures"], "fields": [{"machine_code": "structure_type", "label": "Structure Type", "type": "list", "lookup": "structure_types"}]}'); 
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (22, 'structure_lines', 'Structure Lines', 'Linestring', 0, 'structure_lines.qml', NULL, '{"hierarchy": ["Structures"], "fields": [{"machine_code": "structure_type", "label": "Structure Type", "type": "list", "lookup": "structure_types"}]}');

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (25, 'brat_cis', 'BRAT CIS', 'Point', 0, 'brat_cis.qml', NULL, '{"hierarchy": ["Assessments", "Beaver Dam Building"], "fields": [{"machine_code": "streamside_vegetation", "label": "Streamside Vegetation Suitability", "type": "text"}, {"machine_code": "riparian_vegetation", "label": "Riparian/Upland Vegetation Suitability", "type": "text"}, {"machine_code": "dam_capacity", "label": "Dam Capacity", "type": "text"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (26, 'brat_cis_reaches', 'BRAT CIS Reaches', 'Linestring', 0, 'brat_cis_reaches.qml', NULL, '{"hierarchy": ["Assessments", "Beaver Dam Building"]}');

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (30, 'observation_points', 'Observations', 'Point', 0, 'observation_points.qml', NULL, '{"hierarchy": ["Observations"], "fields": [{"machine_code": "observation_point_type", "label": "Observation Type", "type": "list", "lookup": "observation_point_types"}, {"machine_code": "photo_path", "label": "Photo Path", "type": "attachment"}]}'); 
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (31, 'observation_lines', 'Observations', 'Linestring', 0, 'observation_lines.qml', NULL, '{"hierarchy": ["Observations"], "fields": [{"machine_code": "observation_line_type", "label": "Observation Type", "type": "list", "lookup": "observation_line_types"}]}');
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (32, 'observation_polygons', 'Observations', 'Polygon', 0, 'observation_polygons.qml', NULL, '{"hierarchy": ["Observations"], "fields": [{"machine_code": "observation_polygon_type", "label": "Observation Type", "type": "list", "lookup": "observation_polygon_types"}]}');

INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (33, 'observation_points_dce', 'Observations', 'Point', 0, 'observation_points_dce.qml', NULL, '{"hierarchy": ["Observations", "Other"], "fields": [{"machine_code": "photo_path", "label": "Photo Path", "type": "attachment"}]}'); 
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (34, 'observation_lines_dce', 'Observations', 'Linestring', 0, 'observation_lines_dce.qml', NULL, '{"hierarchy": ["Observations", "Other"]}');
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (35, 'observation_polygons_dce', 'Observations', 'Polygon', 0, 'observation_polygons_dce.qml', NULL, '{"hierarchy": ["Observations", "Other"]}');
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (36, 'structural_elements_points', 'Structural Elements', 'Point', 0, 'structural_elements_points.qml', NULL, '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"machine_code": "structural_element_type", "label": "Type", "type": "list", "lookup": "structural_element_points"}]}' );
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (37, 'structural_elements_lines', 'Structural Elements', 'Linestring', 0, 'structural_elements_lines.qml', NULL, '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"machine_code": "structural_element_type", "label": "Type", "type": "list", "lookup": "structural_element_lines"}]}' );
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (38, 'structural_elements_areas', 'Structural Elements', 'Polygon', 0, 'structural_elements_areas.qml', NULL, '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"machine_code": "structural_element_type", "label": "Type", "type": "list", "lookup": "structural_element_areas"}, {"machine_code": "structure_count", "label": "Structure Count", "type": "integer"}, {"machine_code": "length", "label": "Length", "type": "float"}, {"machine_code": "width", "label": "Width", "type": "float"}, {"machine_code": "height", "label": "Height", "type": "float"}, {"machine_code": "large_wood_count", "label": "Large Wood Count", "type": "integer"}]}' );
INSERT INTO layers(id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (39, 'observation_points_asbuilt', 'Observations', 'Point', 0, 'observation_points_asbuilt.qml', NULL, '{"hierarchy": ["Observations"], "fields": [{"machine_code": "photo_path", "label": "Photo Path", "type": "attachment"}]}'); 

-- Lookup Tables
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description, metadata) VALUES (100, 'lkp_metric_sources', 'Metric Sources', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (101, 'lkp_platform', 'Platform', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (102, 'lkp_mask_types', 'Mask Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (120, 'lkp_design_status', 'Design Status', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (131, 'lkp_representation', 'Representation', 'NoGeometry', 1, 'temp.qml', NULL);
-- -- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (132, 'lkp_profiles', 'Profiles', 'NoGeometry', 1, 'none.qml', NULL);
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (133, 'lkp_units', 'Unit Types', 'NoGeometry', 1, 'none.qml', NULL);

CREATE TABLE method_layers (
    method_id INTEGER NOT NULL REFERENCES methods(id) ON DELETE CASCADE,
    layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,

    CONSTRAINT pk_method_layers PRIMARY KEY (method_id, layer_id)
);

INSERT INTO method_layers (method_id, layer_id) VALUES (1, 1);
-- INSERT INTO method_layers (method_id, layer_id) VALUES (1, 2);
-- INSERT INTO method_layers (method_id, layer_id) VALUES (1, 3);
-- INSERT INTO method_layers (method_id, layer_id) VALUES (1, 4);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 5);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 6);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 7);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 8);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 10);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 11);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 12);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 14);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 15);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 17);

INSERT INTO method_layers (method_id, layer_id) VALUES (1, 25);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 26);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 33);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 34);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 35);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 36);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 37);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 38);

INSERT INTO method_layers (method_id, layer_id) VALUES (5, 19);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 20);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 21);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 22);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 30);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 31);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 32);

INSERT INTO method_layers (method_id, layer_id) VALUES (6, 21);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 22);
INSERT INTO method_layers (method_id, layer_id) VALUES (6, 39);

--dce layers
ALTER TABLE dce_points ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE dce_points ADD COLUMN event_layer_id INTEGER REFERENCES layers(id) ON DELETE CASCADE;
ALTER TABLE dce_points ADD COLUMN metadata TEXT;

CREATE INDEX ix_dce_points_event_id ON dce_points(event_id, event_layer_id);

ALTER TABLE dce_lines ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE dce_lines ADD COLUMN event_layer_id INTEGER REFERENCES layers(id) ON DELETE CASCADE;
ALTER TABLE dce_lines ADD COLUMN metadata TEXT;

CREATE INDEX ix_dce_lines_event_id ON dce_lines(event_id, event_layer_id);

ALTER TABLE dce_polygons ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE dce_polygons ADD COLUMN event_layer_id INTEGER REFERENCES layers(id) ON DELETE CASCADE;
ALTER TABLE dce_polygons ADD COLUMN metadata TEXT;

CREATE INDEX ix_dce_polygons_event_id ON dce_polygons(event_id, event_layer_id);

CREATE TABLE lookup_list_values (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 list_name TEXT NOT NULL,
 list_value TEXT NOT NULL,
 metadata TEXT,
 created_on DATETIME DEFAULT CURRENT_TIMESTAMP);
 
 CREATE UNIQUE INDEX ux_lookup_list_values ON lookup_list_values(list_name, list_value);

-- CREATE TABLE dce_layers (
--     id INTEGER PRIMARY KEY NOT NULL,
--     name TEXT UNIQUE NOT NULL,
--     metadata TEXT
-- );

-- CREATE TABLE protocol_layers (
--     protocol_id INTEGER NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
--     layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
--     metadata TEXT,
--     CONSTRAINT pk_protocol_layers PRIMARY KEY (protocol_id, layer_id)
-- );

-- -- RIM
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 1);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 5);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 8);

-- -- Active Extents
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (2, 6);

-- -- Structural Elements
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 3);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 4);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 1);

-- -- Low Tech Designs
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 19);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 20);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 21);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 22);

-- -- Channel Units
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (6, 23);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (6, 24);

-- CREATE TABLE lkp_metric_sources (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT UNIQUE NOT NULL,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_metric_sources (id, name, description) VALUES (1, 'Calculated', 'Calculated from spatial data');
-- INSERT INTO lkp_metric_sources (id, name, description) VALUES (2, 'Estimated', 'Estimated from other sources or evidence');


CREATE TABLE lkp_context_layer_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    symbology TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (1, 'Aerial imagery', NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (2, 'DEM', 'Shared/dem.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (3, 'Detrended DEM', NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (4, 'Geomorphic Change Detection (GCD)',NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (5, 'Hillshade', 'Shared/Hillshade.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (6, 'Slope Raster','Shared/slope.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (7, 'VBET Evidence','VBET/vbetLikelihood.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (8, 'Other', NULL);

-- so, can these be vector and raster? does it matter?
CREATE TABLE context_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER REFERENCES lkp_context_layer_types(id),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    path TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_guid TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_by TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lkp_event_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO lkp_event_types (id, name, description) VALUES (1, 'Generic Data Capture Event', NULL);
INSERT INTO lkp_event_types (id, name, description) VALUES (2, 'Low Tech Design', NULL);
INSERT INTO lkp_event_types (id, name, description) VALUES (3, 'As-Built survey', NULL);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    event_type_id INT REFERENCES lkp_event_types(id),
    platform_id INTEGER REFERENCES lkp_platform(id),
    representation_id INTEGER REFERENCES lkp_representation(id),
    metadata TEXT,
    date_text TEXT,
    start_year INT,
    start_month INT,
    start_day INT,
    end_year INT,
    end_month INT,
    end_day INT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lkp_platform (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_platform (id, name) VALUES (1, 'Desktop');
INSERT INTO lkp_platform (id, name) VALUES (2, 'Field');

CREATE TABLE lkp_representation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_representation (id, name) VALUES (1, 'Current');
INSERT INTO lkp_representation (id, name) VALUES (2, 'Historic');
INSERT INTO lkp_representation (id, name) VALUES (3, 'Future');

CREATE TABLE event_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE
);
CREATE UNIQUE index ux_event_layers ON event_layers(event_id, layer_id);

CREATE TABLE lkp_raster_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    symbology TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_raster_types (id, name, symbology) VALUES (1, 'Other', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (2, 'Basemap', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (3, 'Detrended Surface', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (4, 'Digital Elevation Model (DEM)', 'Shared/dem.qml');
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (5, 'Valley Bottom Evidence', 'VBET/vbetLikelihood.qml');
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (6, 'Hillshade', 'Shared/Hillshade.qml');


CREATE TABLE rasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raster_type_id INTEGER REFERENCES lkp_raster_types(id),
    is_context Boolean DEFAULT 0,
    name TEXT UNIQUE NOT NULL,
    path TEXT UNIQUE NOT NULL,
    -- type will likely be populated from a lookup. e.g., imagery, dem, lidar, etc....
    type TEXT,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_rasters_raster_type_id ON rasters(raster_type_id);


CREATE TABLE lkp_scratch_vector_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_scratch_vector_types (id, name) VALUES (1, 'Other');

CREATE TABLE scratch_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vector_type_id INTEGER REFERENCES lkp_scratch_vector_types(id),
    name TEXT UNIQUE NOT NULL,
    fc_name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_scratch_vectors_vector_type_id ON scratch_vectors(vector_type_id);


CREATE TABLE event_rasters (
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    raster_id INTEGER REFERENCES rasters(id) ON DELETE CASCADE,
    
    CONSTRAINT pk_event_rasters PRIMARY KEY (event_id, raster_id)
);

CREATE TABLE lkp_mask_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- need to review these types. I'm not totally sure that this is necessary in a table.
INSERT INTO lkp_mask_types (id, name) VALUES (1, 'Area of Interest (AOI)');
INSERT INTO lkp_mask_types (id, name) VALUES (2, 'Regular Mask');
INSERT INTO lkp_mask_types (id, name) VALUES (3, 'Directional Mask');

CREATE TABLE masks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    mask_type_id INTEGER NOT NULL REFERENCES lkp_mask_types(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- AOI features refer to the AOI mask that they belong to
ALTER TABLE aoi_features ADD COLUMN mask_id INTEGER REFERENCES masks(id) ON DELETE CASCADE;
ALTER TABLE aoi_features ADD COLUMN metadata TEXT;

-- Regular masks refer to the mask that they belong to and have a display label
ALTER TABLE mask_features ADD COLUMN mask_id INTEGER REFERENCES masks(id) ON DELETE CASCADE;
ALTER TABLE mask_features ADD COLUMN display_label TEXT;
ALTER TABLE mask_features ADD COLUMN display_order INTEGER;
-- ALTER TABLE mask_features ADD COLUMN name TEXT;
ALTER TABLE mask_features ADD COLUMN position INTEGER;
ALTER TABLE mask_features ADD COLUMN description TEXT;
ALTER TABLE mask_features ADD COLUMN metadata TEXT;

-- units
CREATE TABLE lkp_units (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL UNIQUE,
	display_name TEXT NOT NULL UNIQUE,
	conversion REAL,
	conversion_unit_id INTEGER,
	dimension TEXT,
	description TEXT,
    metatdata TEXT,
	created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (1, 'Meters', 'm', NULL, NULL, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (2, 'Square Meters', '㎡', NULL, NULL, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (3, 'Cubic Meters', 'm³', NULL, NULL, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (4, 'Feet', 'ft', 0.3048, 1, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (5, 'Square Feet', 'sqft', 0.092903, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (6, 'Cubic Feet', 'ft³', 0.0283168, 3, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (7, 'Hectares', 'ha', 10000, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (8, 'Acres', 'ac', 4046.86, 2, 'area');

CREATE TABLE calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_function TEXT
);

INSERT INTO calculations (id, name, metric_function) VALUES (1, 'count', 'count');
INSERT INTO calculations (id, name, metric_function) VALUES (2, 'length', 'length');
INSERT INTO calculations (id, name, metric_function) VALUES (3, 'area', 'area');
INSERT INTO calculations (id, name, metric_function) VALUES (4, 'sinuosity', 'sinuosity');
INSERT INTO calculations (id, name, metric_function) VALUES (5, 'gradient', 'gradient');

CREATE TABLE metric_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO metric_levels (id, name) VALUES (1, 'Metric');
INSERT INTO metric_levels (id, name) VALUES (2, 'Indicator');


CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculations(id),
    default_level_id INTEGER REFERENCES metric_levels(id),
    unit_id INTEGER REFERENCES lkp_units(id),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    definition_url TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_params TEXT
);

INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (1, 1, 'dam and jam count', 1, NULL, '{"layers": ["dams","jams"]}', '{"min_value": 0}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (2, NULL, 'Percent Active Floodplain', 1, NULL, NULL, '{"min_value": 0, "max_value": 100, "tolerance": 0.25}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (3, 5, 'Centerline Gradient', 2, NULL, '{"layers": ["profile_centerlines"], "rasters": ["Digital Elevation Model (DEM)"]}', '{"precision": 4, "tolerance": 0.1}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (4, 2, 'Dam Crest Length', 1, 1, '{"layers": ["dam_crests"]}', '{"min_value": 0, "max_value": 10000, "precision": 2, "tolerance": 0.1}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (5, 3, 'Valley Bottom Area', 1, 2, '{"layers": ["valley_bottoms"]}', NULL);
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (6, 4, 'Centelrine Sinuosity', 1,  NULL, '{"layers": ["profile_centerlines"]}', '{"min_value": 1, "precision": 4, "tolerance": 0.1}');

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    mask_id INTEGER NOT NULL REFERENCES masks(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_analyses_mask_id ON analyses(mask_id);

CREATE TABLE analysis_metrics (
    analysis_id INT NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    metric_id INT NOT NULL REFERENCES metrics(id),
    level_id INT NOT NULL REFERENCES metric_levels(id),

    CONSTRAINT pk_analysis_metrics PRIMARY KEY (analysis_id, metric_id)
);


CREATE TABLE metric_values (
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    mask_feature_id INTEGER REFERENCES mask_features(fid) ON DELETE CASCADE,
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

    CONSTRAINT pk_metric_values PRIMARY KEY (analysis_id, event_id, mask_feature_id, metric_id)
);

CREATE INDEX fx_metric_values_analysis_id ON metric_values(analysis_id);
CREATE INDEX fx_metric_values_mask_feature_id ON metric_values(mask_feature_id);
CREATE INDEX fx_metric_values_metric_id ON metric_values(metric_id);
CREATE INDEX fx_metric_values_event_id ON metric_values(event_id);

-- dam and jam surveys
CREATE TABLE lkp_structure_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_source (id, name) VALUES (1, 'Natural');
INSERT INTO lkp_structure_source (id, name) VALUES (2, 'Artificial');
INSERT INTO lkp_structure_source (id, name) VALUES (3, 'Unknown');


CREATE TABLE lkp_dam_integrity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_dam_integrity (id, name) VALUES (1, 'Intact');
INSERT INTO lkp_dam_integrity (id, name) VALUES (3, 'Blown');
INSERT INTO lkp_dam_integrity (id, name) VALUES (2, 'Breached');
INSERT INTO lkp_dam_integrity (id, name) VALUES (4, 'Buried');
INSERT INTO lkp_dam_integrity (id, name) VALUES (5, 'Flooded');
INSERT INTO lkp_dam_integrity (id, name) VALUES (6, 'NA');

CREATE TABLE lkp_beaver_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_beaver_maintenance (id, name) VALUES (1, 'None');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (2, 'Old');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (3, 'Fresh');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (4, 'NA');

-- -- brat vegetation
-- CREATE TABLE lkp_brat_vegetation_types (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL UNIQUE,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (1, 'Preferred');
-- INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (2, 'Suitable');
-- INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (3, 'Moderately Suitable');
-- INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (4, 'Barely Suitable');
-- INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (5, 'Unsuitable');

-- ALTER TABLE brat_vegetation ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE brat_vegetation ADD COLUMN type_id INTEGER REFERENCES lkp_brat_vegetation_types(id) ON DELETE CASCADE;
-- ALTER TABLE brat_vegetation ADD COLUMN metadata TEXT;

-- -- BRAT base Stream power
-- CREATE TABLE lkp_brat_base_streampower (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL UNIQUE,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_brat_base_streampower (id, name) VALUES (1, 'Probably can build dam');
-- INSERT INTO lkp_brat_base_streampower (id, name) VALUES (2, 'Can build dam');
-- INSERT INTO lkp_brat_base_streampower (id, name) VALUES (3, 'Can build dam (saw evidence of recent dams)');
-- INSERT INTO lkp_brat_base_streampower (id, name) VALUES (4, 'Could build dam at one time (saw evidence of relic dams)');
-- INSERT INTO lkp_brat_base_streampower (id, name) VALUES (5, 'Cannot build dam (streampower really high)');

-- -- BRAT 2 year flood stream power
-- CREATE TABLE lkp_brat_high_streampower (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL UNIQUE,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_brat_high_streampower (id, name) VALUES (1, 'Blowout');
-- INSERT INTO lkp_brat_high_streampower (id, name) VALUES (2, 'Occasional Breach');
-- INSERT INTO lkp_brat_high_streampower (id, name) VALUES (3, 'Occasional Blowout');
-- INSERT INTO lkp_brat_high_streampower (id, name) VALUES (4, 'Dam Persists');


-- CREATE TABLE lkp_brat_slope (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL UNIQUE,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_brat_slope (id, name) VALUES (1, 'So steep they cannot build a dam (e.g. > 20% slope)');
-- INSERT INTO lkp_brat_slope (id, name) VALUES (2, 'Probably can build dam');
-- INSERT INTO lkp_brat_slope (id, name) VALUES (3, 'Can build dam (inferred)');
-- INSERT INTO lkp_brat_slope (id, name) VALUES (4, 'Can build dam (evidence or current or past dams)');
-- INSERT INTO lkp_brat_slope (id, name) VALUES (5, 'Really flat (can build dam, but might not need as many as one dam might back up water > 0.5 km)');

-- CREATE TABLE lkp_brat_dam_density (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL UNIQUE,
--     description TEXT,
--     created_on DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (1, 'None', '(no dams)');
-- INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (2, 'Rare', '(0-1 dams/km)');
-- INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (3, 'Occasional', '(1-4 dams/km)');
-- INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (4, 'Frequent', '(5-15 dams/km)');
-- INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (5, 'Pervasive', '(15-40 dams/km)');

-- CREATE TABLE lkp_brat_vegetation_cis
-- (
--     rule_id INTEGER PRIMARY KEY AUTOINCREMENT ,
--     streamside_veg_id INT NOT NULL REFERENCES lkp_brat_vegetation_types (id) ON DELETE CASCADE,
--     riparian_veg_id INT NOT NULL REFERENCES  lkp_brat_vegetation_types (id) ON DELETE CASCADE,
--     output_id INT NOT NULL REFERENCES lkp_brat_dam_density(id) ON DELETE CASCADE
-- );
-- CREATE INDEX ux_lkp_brat_vegetation_cis ON lkp_brat_vegetation_cis(streamside_veg_id, riparian_veg_id, output_id);

-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (1, 5, 5, 1);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (2, 4, 5, 2);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (3, 3, 5, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (4, 2, 5, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (5, 1, 5, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (6, 5, 4, 2);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (7, 4, 4, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (8, 3, 4, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (9, 2, 4, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (10, 1, 4, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (11, 5, 3, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (12, 4, 3, 2);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (13, 3, 3, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (14, 2, 3, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (15, 1, 3, 5);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (16, 5, 2, 2);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (17, 4, 2, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (18, 3, 2, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (19, 2, 2, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (20, 1, 2, 5);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (21, 5, 1, 3);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (22, 4, 1, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (23, 3, 1, 4);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (24, 2, 1, 5);
-- INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (25, 1, 1, 5);

-- CREATE TABLE lkp_brat_combined_cis (
--     rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     veg_density_id INTEGER NOT NULL REFERENCES lkp_brat_vegetation_cis(rule_id) ON DELETE CASCADE,
--     base_streampower_id INTEGER NOT NULL REFERENCES lkp_brat_base_streampower(id) ON DELETE CASCADE,
--     high_streampower_id INTEGER NOT NULL REFERENCES lkp_brat_high_streampower(id) ON DELETE CASCADE,
--     slope_id INTEGER NOT NULL REFERENCES  lkp_brat_slope(id) ON DELETE CASCADE,
--     output_id INTEGER NOT NULL REFERENCES lkp_brat_dam_density(id) ON DELETE CASCADE
-- );
-- CREATE INDEX ux_lkp_brat_combined_cis ON lkp_brat_combined_cis(veg_density_id, base_streampower_id, high_streampower_id, slope_id);

-- --value combinations that produce an output of 'None' are not stored in this table
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (1, 2, 2, 4, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (2, 2, 2, 4, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (3, 2, 2, 4, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (4, 2, 2, 4, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (5, 2, 2, 4, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (6, 3, 2, 4, 1, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (7, 3, 2, 4, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (8, 3, 2, 4, 3, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (9, 3, 2, 4, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (10, 3, 2, 4, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (11, 4, 2, 4, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (12, 4, 2, 4, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (13, 5, 2, 4, 5, 5);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (14, 5, 2, 4, 4, 5);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (15, 5, 2, 4, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (16, 2, 2, 2, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (17, 2, 2, 2, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (18, 2, 2, 2, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (19, 2, 2, 2, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (20, 2, 2, 2, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (21, 3, 2, 2, 1, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (22, 3, 2, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (23, 3, 2, 2, 3, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (24, 3, 2, 2, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (25, 3, 2, 2, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (26, 4, 2, 2, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (27, 4, 2, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (28, 5, 2, 2, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (29, 5, 2, 2, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (30, 5, 2, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (31, 2, 2, 3, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (32, 2, 2, 3, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (33, 2, 2, 3, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (34, 2, 2, 3, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (35, 2, 2, 3, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (36, 3, 2, 3, 1, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (37, 3, 2, 3, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (38, 3, 2, 3, 3, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (39, 3, 2, 3, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (40, 3, 2, 3, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (41, 4, 2, 3, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (42, 4, 2, 3, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (43, 5, 2, 3, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (44, 5, 2, 3, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (45, 5, 2, 3, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (46, 3, 2, 1, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (47, 3, 2, 1, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (48, 3, 2, 1, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (49, 3, 2, 1, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (50, 3, 2, 1, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (51, 4, 2, 1, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (52, 5, 2, 1, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (53, 5, 2, 1, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (54, 5, 2, 1, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (55, 2, 1, 2, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (56, 2, 1, 2, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (57, 2, 1, 2, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (58, 2, 1, 2, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (59, 2, 1, 2, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (60, 3, 1, 2, 1, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (61, 3, 1, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (62, 3, 1, 2, 3, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (63, 3, 1, 2, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (64, 3, 1, 2, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (65, 4, 1, 2, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (66, 4, 1, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (67, 5, 1, 2, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (68, 5, 1, 2, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (69, 5, 1, 2, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (70, 2, 1, 3, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (71, 2, 1, 3, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (72, 2, 1, 3, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (73, 2, 1, 3, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (74, 2, 1, 3, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (75, 3, 1, 3, 1, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (76, 3, 1, 3, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (77, 3, 1, 3, 3, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (78, 3, 1, 3, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (79, 3, 1, 3, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (80, 4, 1, 3, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (81, 4, 1, 3, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (82, 5, 1, 3, 5, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (83, 5, 1, 3, 4, 4);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (84, 5, 1, 3, 2, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (85, 3, 1, 1, 1, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (86, 3, 1, 1, 2, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (87, 3, 1, 1, 3, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (88, 3, 1, 1, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (89, 3, 1, 1, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (90, 4, 1, 1, 4, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (91, 5, 1, 1, 5, 2);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (92, 5, 1, 1, 4, 3);
-- INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (93, 5, 1, 1, 2, 2);

-- -- Alter the BRAT CIS Feature Class table
-- ALTER TABLE brat_cis ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE brat_cis ADD COLUMN observer_name TEXT;
-- ALTER TABLE brat_cis ADD COLUMN reach_id TEXT;
-- ALTER TABLE brat_cis ADD COLUMN observation_date DATE;
-- ALTER TABLE brat_cis ADD COLUMN reach_length FLOAT;
-- ALTER TABLE brat_cis ADD COLUMN notes TEXT;
-- ALTER TABLE brat_cis ADD COLUMN metadata TEXT;

-- ALTER TABLE brat_cis ADD COLUMN streamside_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
-- ALTER TABLE brat_cis ADD COLUMN riparian_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
-- ALTER TABLE brat_cis ADD COLUMN veg_density_id INT REFERENCES lkp_brat_dam_density(id);

-- ALTER TABLE brat_cis ADD COLUMN base_streampower_id INT REFERENCES lkp_brat_base_streampower(id);
-- ALTER TABLE brat_cis ADD COLUMN high_streampower_id INT REFERENCES lkp_brat_high_streampower(id);

-- ALTER TABLE brat_cis ADD COLUMN slope_id INT REFERENCES lkp_brat_slope(id);

-- ALTER TABLE brat_cis ADD COLUMN combined_density_id INT REFERENCES lkp_brat_dam_density(id);

-- -- Alter the Brat CIS Reaches feature class
-- ALTER TABLE brat_cis_reaches ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE brat_cis_reaches ADD COLUMN observer_name TEXT;
-- ALTER TABLE brat_cis_reaches ADD COLUMN reach_id TEXT;
-- ALTER TABLE brat_cis_reaches ADD COLUMN observation_date DATE;
-- ALTER TABLE brat_cis_reaches ADD COLUMN reach_length FLOAT;
-- ALTER TABLE brat_cis_reaches ADD COLUMN notes TEXT;
-- ALTER TABLE brat_cis_reaches ADD COLUMN metadata TEXT;

-- ALTER TABLE brat_cis_reaches ADD COLUMN streamside_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
-- ALTER TABLE brat_cis_reaches ADD COLUMN riparian_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
-- ALTER TABLE brat_cis_reaches ADD COLUMN veg_density_id INT REFERENCES lkp_brat_dam_density(id);

-- ALTER TABLE brat_cis_reaches ADD COLUMN base_streampower_id INT REFERENCES lkp_brat_base_streampower(id);
-- ALTER TABLE brat_cis_reaches ADD COLUMN high_streampower_id INT REFERENCES lkp_brat_high_streampower(id);

-- ALTER TABLE brat_cis_reaches ADD COLUMN slope_id INT REFERENCES lkp_brat_slope(id);

-- ALTER TABLE brat_cis_reaches ADD COLUMN combined_density_id INT REFERENCES lkp_brat_dam_density(id);
----------------------------------------------------------------------------------------------------------------

-- Design Lookup Tables
CREATE TABLE lkp_design_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_design_status (id, name, description) VALUES (1, 'Preliminary Desktop', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (2, 'Desktop Analysis (Remote)', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (3, 'Provisional', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (4, 'In Review', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (5, 'Final', NULL);

CREATE TABLE lkp_design_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_design_sources (id, name, description) VALUES (1, 'Previous Site Visit', NULL);
INSERT INTO lkp_design_sources (id, name, description) VALUES (2, 'Desktop Analysis (Remote)', NULL);
INSERT INTO lkp_design_sources (id, name, description) VALUES (3, 'Field Work', NULL);

-- Master Lookup Lists --
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (1, 'zoi_types_orig', 'Increase Channel Complexity', '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (2, 'zoi_types_orig', 'Accelerate Incision Recovery', '{"description": "Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (3, 'zoi_types_orig', 'Lateral Channel Migration', '{"description": "Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (4, 'zoi_types_orig', 'Increase Floodplain Connectivity', '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (5, 'zoi_types_orig', 'Facilitate Beaver Translocation', '{"description": "Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (6, 'zoi_types_orig', 'Other', '{"description": "Area of hydraulic feature creation (e.g., eddy, shear zone, hydraulic jet)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (7, 'structure_types_orig', 'BDA Large', '{"mimics_id": 1}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (8, 'structure_types_orig', 'BDA Small', '{"mimics_id": 1}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (9, 'structure_types_orig', 'BDA Postless', '{"mimics_id": 1}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (10, 'structure_types_orig', 'PALS Mid-Channel', '{"mimics_id": 2}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (11, 'structure_types_orig', 'PALS Bank Attached', '{"mimics_id": 2}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (12, 'structure_types_orig', 'Wood Jam', '{"mimics_id": 2}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (13, 'structure_types_orig', 'Other', '{"mimics_id": 3}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (14, 'structure_mimics', 'Beaver Dam', '{"description": "Structure has been designed to mimic the form and function of a beaver dam"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (15, 'structure_mimics', 'Wood Jam', '{"description": "Structure has been designed to mimic the form and function of a wood jam or piece of woody debris"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (16, 'structure_mimics', 'Other', '{"description": "Structure does not mimic a beaver dam, wood jam, or woody debris"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (17, 'zoi_stages', 'Baseflow', '{"description": "Extent is the expected influence during or in response to baseflow discharge"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (18, 'zoi_stages', 'Typical Flood', '{"description": "Extent is the expected influence during or in response to a typical flood event (e.g., 5 year recurrence interval)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (19, 'zoi_stages', 'Large Flood', '{"description": "Extent the expected influence during or in response to a large flood event (e.g., 20 year recurrence interval)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (20, 'zoi_stages', 'Other', '{"description": "Extent is not related to flood event"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (21, 'observation_point_types', "Logistics", '{"description": "Observation point is used to record logistical information about the site (e.g., access, parking, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (22, 'observation_point_types', "Riverscape Feature", '{"description": "Observation point is used to record information about a riverscape feature (e.g., riffle, pool, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (23, 'observation_point_types', "Design Consideration", '{"description": "Observation point is used to record information about a design consideration (e.g., structure location, structure type, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (24, 'observation_point_types', "Building Materials", '{"description": "Observation point is used to record information about building source materials (e.g., wood, rock, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (25, 'observation_point_types', "Photo Observation", '{"description": "Observation point is used to record information about a photo observation (e.g., photo point, photo direction, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (26, 'observation_point_types', "Caution", '{"description": "Observation point is used to record information about a cautionary note (e.g., safety, access, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (27, 'observation_point_types', "Other", '{"description": "Observation point is used to record information that does not fit into any other category"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (28, 'observation_line_types', "Road", '{"description": "Observation line is used to record information about a road (e.g., road name, road condition, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (29, 'observation_line_types', "Logistics", '{"description": "Observation line is used to record logistical information about the site (e.g., access, parking, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (30, 'observation_line_types', "Riverscape Feature", '{"description": "Observation line is used to record information about a riverscape feature (e.g., riffle, pool, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUEs (31, 'observation_line_types', "Caution", '{"description": "Observation line is used to record information about a cautionary note (e.g., safety, access, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (32, 'observation_line_types', "Other", '{"description": "Observation line is used to record information that does not fit into any other category"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (33, 'observation_polygon_types', "Logistics", '{"description": "Observation polygon is used to record logistical information about the site (e.g., access, parking, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (34, 'observation_polygon_types', "Building Materials", '{"description": "Observation polygon is used to record information about building source materials (e.g., wood, rock, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (35, 'observation_polygon_types', "Infrastructure", '{"description": "Observation polygon is used to record information about infrastructure (e.g., bridge, culvert, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (36, 'observation_polygon_types', "Caution", '{"description": "Observation polygon is used to record information about a cautionary note (e.g., safety, access, etc.)"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (37, 'observation_polygon_types', "Other", '{"description": "Observation polygon is used to record information that does not fit into any other category"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (38, 'zoi_types', "Complex: Increase Floodplain Connectivity", '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (39, 'zoi_types', "Complex: Overbank Flow Dispersal", '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (40, 'zoi_types', "Complex: Aggradation and Avulsion", '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}'); 
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (41, 'zoi_types', "Complex: Side-Channel Connection", '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (42, 'zoi_types', "Complex: Riparian/Wetland Expansion", '{"description": "Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (43, 'zoi_types', "Complex: Facilitate Beaver Translocation", '{"description": "Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (44, 'zoi_types', "Complex: Pond/Wetland Creation", '{"description": "Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (45, 'zoi_types', "Complex: Accelerate Incision Recovery", '{"description": "Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (46, 'zoi_types', "Complex: Lateral Channel Migration", '{"description": "Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (47, 'zoi_types', "Complex: Widening and Aggradation", '{"description": "Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (48, 'zoi_types', "Complex: Increase Channel Complexity", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (49, 'zoi_types', "Complex: Headcut Arrest", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (50, 'zoi_types', "Complex: Cover/Complexity", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (51, 'zoi_types', "Structure: Hydraulic - Eddy", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (52, 'zoi_types', "Structure: Hydraulic - Splitting Flow", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (53, 'zoi_types', "Structure: Hydraulic - Shunting Flow", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (54, 'zoi_types', "Structure: Hydraulic - Ponding Flow", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (55, 'zoi_types', "Structure: Hydraulic - Overflow", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (56, 'zoi_types', "Structure: Hydraulic - Constriction Jet", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (57, 'zoi_types', "Structure: Hydraulic - Divergent Flow", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (58, 'zoi_types', "Structure: Geomorphic - Erode Bank", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (59, 'zoi_types', "Structure: Geomorphic - Erosion from return flow headcut", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (60, 'zoi_types', "Structure: Geomorphic - Erosion from plunge", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (61, 'zoi_types', "Structure: Geomorphic - Erosion from convergent jet", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (62, 'zoi_types', "Structure: Geomorphic - Erosion of bar edge", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (63, 'zoi_types', "Structure: Geomorphic - Deposition overbank", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (64, 'zoi_types', "Structure: Geomorphic - Deposition of bar", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (65, 'zoi_types', "Structure: Geomorphic - Deposition in upstream backwater", '{"description": "Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (66, 'zoi_types', "Structure: Scout Pool Formation", '{"description": "Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders"}');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (67, 'structure_types', 'Secondary BDA', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (68, 'structure_types', 'BDA', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (69, 'structure_types', 'Primary BDA', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (70, 'structure_types', 'BDA Large', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (71, 'structure_types', 'BDA Small', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (72, 'structure_types', 'BDA Postless', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (73, 'structure_types', 'PALS', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (74, 'structure_types', 'PALS - Bank Attached', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (75, 'structure_types', 'PALS - Right Bank Attached', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (76, 'structure_types', 'PALS - Left Bank Attached', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (77, 'structure_types', 'PALS - Bank Blaster', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (78, 'structure_types', 'PALS - Constriction Jet', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (79, 'structure_types', 'PALS - Mid Channel', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (80, 'structure_types', 'PALS - Rhino', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (81, 'structure_types', 'Rhino', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (82, 'structure_types', 'PALS - Channel Spanning', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (83, 'structure_types', 'ALS', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (84, 'structure_types', 'ALS - Bank Attached', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (85, 'structure_types', 'ALS - Bank Blaster', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (86, 'structure_types', 'ALS - Mid Channel', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (87, 'structure_types', 'ALS - Rhino', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (88, 'structure_types', 'ALS - Channel Spanning', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (89, 'structure_types', 'Wood Jam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (90, 'structure_types', 'Leaky Dam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (91, 'structure_types', 'One Rock Dam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (92, 'structure_types', 'Zuni Bowl', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (93, 'structure_types', 'Spreaders', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (94, 'structure_types', 'Floodplain BDA', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (95, 'structure_types', 'Sedge Plugs', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (96, 'structure_types', 'Tight PALS (BDA without sod)', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (97, 'structure_types', 'Full Tree', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (98, 'structure_types', 'Bag Plugs', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (99, 'structure_types', 'Headcut Treatment', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (100, 'structure_types', 'Floodplain LWD', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (101, 'structure_types', 'Startegic Felling', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (102, 'structure_types', 'Postline Wicker Weave', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (103, 'structure_types', 'Grip Hoist Tree', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (104, 'structure_types', 'Fell Tree', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (105, 'structure_types', 'Post and Brush Plug', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (106, 'structure_types', 'Tree Dam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (107, 'structure_types', 'Tree Plug', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (108, 'structure_types', 'Vanes', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (109, 'structure_types', 'Wicker Weirs', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (110, 'inundation_extent_types', 'Ponded','');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (111, 'inundation_extent_types', 'Free Flowing','');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (112, 'inundation_extent_types', 'Overflow','');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (113, 'structural_element_lines', 'Dam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (114, 'structural_element_areas', 'Jam', ''); 
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (115, 'structural_element_points', 'Dam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (116, 'structural_element_points', 'Dam Complex', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (117, 'structural_element_points', 'Jam', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (118, 'structural_element_points', 'Jam Complex', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (119, 'structural_element_points', 'Other', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (120, 'structural_element_points', 'Root Mass', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (121, 'active_extent_types', 'Active', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (122, 'active_extent_types', 'Inactive', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (123, 'centerline_types', 'Non-Primary', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (124, 'centerline_types', 'Primary', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (125, 'centerline_descriptions', 'Centerline', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (126, 'centerline_descriptions', 'Thalweg', '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (127, 'geomorphic_units_tier2_types', "Bowl", '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (128, 'geomorphic_units_tier2_types', "Trough", '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (129, 'geomorphic_units_tier2_types', "Plane", '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (130, 'geomorphic_units_tier2_types', "Saddle", '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (131, 'geomorphic_units_tier2_types', "Mound", '');
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (132, 'junction_types', "Confluence (Anabranch)", "Confluence (Anabranch)");
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (133, 'junction_types', "Confluence (Tributary)", "Confluence (Tributary)");
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (134, 'junction_types', "Diffluence", "Diffluence");
INSERT INTO lookup_list_values (id, list_name, list_value, metadata) VALUES (135, 'junction_types', "Channel Head", "Channel Head");



-- Design Spatial Table Fields and Relationships
-- ALTER TABLE zoi ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE zoi ADD COLUMN type_id INTEGER REFERENCES zoi_types(id);
-- ALTER TABLE zoi ADD COLUMN stage_id INTEGER REFERENCES lkp_zoi_stage(id);
-- ALTER TABLE zoi ADD COLUMN description TEXT;
-- ALTER TABLE zoi ADD COLUMN created DATETIME;
-- ALTER TABLE zoi ADD COLUMN metadata TEXT;

-- ALTER TABLE complexes ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE complexes ADD COLUMN name TEXT;
-- ALTER TABLE complexes ADD COLUMN initial_condition TEXT;
-- ALTER TABLE complexes ADD COLUMN target_condition TEXT;
-- ALTER TABLE complexes ADD COLUMN description TEXT;
-- ALTER TABLE complexes ADD COLUMN created DATETIME;
-- ALTER TABLE complexes ADD COLUMN metadata TEXT;

-- ALTER TABLE structure_lines ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(id);
-- ALTER TABLE structure_lines ADD COLUMN name TEXT;
-- ALTER TABLE structure_lines ADD COLUMN description TEXT;
-- ALTER TABLE structure_lines ADD COLUMN created DATETIME;
-- ALTER TABLE structure_lines ADD COLUMN metadata TEXT;

-- ALTER TABLE structure_points ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
-- ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(id);
-- ALTER TABLE structure_points ADD COLUMN name TEXT;
-- ALTER TABLE structure_points ADD COLUMN description TEXT;
-- ALTER TABLE structure_points ADD COLUMN created DATETIME;
-- ALTER TABLE structure_points ADD COLUMN metadata TEXT;

-- pour points and catchments
ALTER TABLE pour_points ADD COLUMN name TEXT;
ALTER TABLE pour_points ADD COLUMN description TEXT;
ALTER TABLE pour_points ADD COLUMN latitude FLOAT;
ALTER TABLE pour_points ADD COLUMN longitude FLOAT;
ALTER TABLE pour_points ADD COLUMN basin_characteristics TEXT;
ALTER TABLE pour_points ADD COLUMN flow_statistics TEXT;
ALTER TABLE pour_points ADD COLUMN metadata TEXT;

ALTER TABLE catchments ADD COLUMN pour_point_id INT REFERENCES pour_points(fid) ON DELETE CASCADE;
ALTER TABLE catchments ADD COLUMN metadata TEXT;

-- stream gages
ALTER TABLE stream_gages ADD COLUMN site_code TEXT;
ALTER TABLE stream_gages ADD COLUMN site_name TEXT;
ALTER TABLE stream_gages ADD COLUMN site_type TEXT;
ALTER TABLE stream_gages ADD COLUMN site_datum TEXT;
ALTER TABLE stream_gages ADD COLUMN huc TEXT;
ALTER TABLE stream_gages ADD COLUMN agency TEXT;
ALTER TABLE stream_gages ADD COLUMN metadata TEXT;
ALTER TABLE stream_gages ADD COLUMN latitude REAL;
ALTER TABLE stream_gages ADD COLUMN longitude REAL;
CREATE UNIQUE INDEX ux_stream_gages_site_code ON stream_gages(site_code);
CREATE INDEX ix_stream_gages_site_name ON stream_gages(site_name);
CREATE INDEX ix_stream_gages_huc_cd ON stream_gages(huc);

-- stream gage discharge
CREATE TABLE stream_gage_discharges
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_gage_id INTEGER REFERENCES stream_gages(fid) ON DELETE CASCADE,
    measurement_date DATETIME,
    discharge REAL,
    discharge_code TEXT,
    gage_height REAL,
    gage_height_code TEXT,
    metadata TEXT,

    UNIQUE (stream_gage_id, measurement_date)
);
CREATE INDEX fx_stream_gage_discharges ON stream_gage_discharges(stream_gage_id);
-- CREATE INDEX ux_stream_gage_discharges ON stream_gage_discharges(stream_gage_id, measurement_date);

-- Profiles
CREATE TABLE profiles
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    profile_type_id INTEGER NOT NULL,-- REFERENCES lkp_mask_types(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- profile features refer to the profile that they belong to
ALTER TABLE profile_features ADD COLUMN profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE profile_features ADD COLUMN display_label TEXT;
ALTER TABLE profile_features ADD COLUMN description TEXT;
ALTER TABLE profile_features ADD COLUMN metadata TEXT;

-- centerlines are generated from the centerline tool
ALTER TABLE profile_centerlines ADD COLUMN profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE profile_centerlines ADD COLUMN display_label TEXT;
ALTER TABLE profile_centerlines ADD COLUMN description TEXT;
ALTER TABLE profile_centerlines ADD COLUMN metadata TEXT;

-- Cross Sections
CREATE TABLE cross_sections
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- profile features refer to the profile that they belong to
ALTER TABLE cross_section_features ADD COLUMN cross_section_id INTEGER REFERENCES cross_sections(id) ON DELETE CASCADE;
ALTER TABLE cross_section_features ADD COLUMN sequence INTEGER;
ALTER TABLE cross_section_features ADD COLUMN distance REAL;
ALTER TABLE cross_section_features ADD COLUMN display_label TEXT;
ALTER TABLE cross_section_features ADD COLUMN description TEXT;
ALTER TABLE cross_section_features ADD COLUMN metadata TEXT;

-- add to geopackage contents
-- this is only necessary for non-spatial tables created using ddl.
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('analyses', 'attributes', 'analyses', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('analysis_metrics', 'attributes', 'analysis_metrics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocols', 'attributes', 'protocols', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocol_methods', 'attributes', 'protocol_methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('methods', 'attributes', 'methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('method_layers', 'attributes', 'method_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('layers', 'attributes', 'layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('context_layers', 'attributes', 'context_layers', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocol_layers', 'attributes', 'protocol_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('projects', 'attributes', 'projects', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('events', 'attributes', 'events', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_layers', 'attributes', 'event_layers', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_methods', 'attributes', 'event_methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_rasters', 'attributes', 'event_rasters', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('masks', 'attributes', 'masks', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('calculations', 'attributes', 'calculations', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metrics', 'attributes', 'metrics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metric_levels', 'attributes', 'metric_levels', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metric_values', 'attributes', 'metric_values', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('scratch_vectors', 'attributes', 'scratch_vectors', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('stream_gage_discharges', 'attributes', 'stream_gage_discharges', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('rasters', 'attributes', 'rasters', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('migrations', 'attributes', 'migrations', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('profiles', 'attributes', 'profiles', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('cross_sections', 'attributes', 'cross_sections', 0);

-- -- LOOKUP TABLES
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_metric_sources', 'attributes', 'lkp_metric_sources', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_platform', 'attributes', 'lkp_platform', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_representation', 'attributes', 'lkp_representation', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_mask_types', 'attributes', 'lkp_mask_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_source', 'attributes', 'lkp_structure_source', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_dam_integrity', 'attributes', 'lkp_dam_integrity', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_beaver_maintenance', 'attributes', 'lkp_beaver_maintenance', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_thalweg_types', 'attributes', 'lkp_thalweg_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_junction_types', 'attributes', 'lkp_junction_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_geomorphic_unit_types', 'attributes', 'lkp_geomorphic_unit_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_vegetation_extent_types', 'attributes', 'lkp_vegetation_extent_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_cem_phase_types', 'attributes', 'lkp_cem_phase_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_floodplain_accessibility_types', 'attributes', 'lkp_floodplain_accessibility_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_vegetation_types', 'attributes', 'lkp_brat_vegetation_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_context_layer_types', 'attributes', 'lkp_context_layer_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_channel', 'attributes', 'lkp_primary_channel', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_unit', 'attributes', 'lkp_primary_unit', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_forced', 'attributes', 'lkp_structure_forced', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_channel_unit_types', 'attributes', 'lkp_channel_unit_types', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_raster_types', 'attributes', 'lkp_raster_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lookup_list_values', 'attributes', 'lookup_list_values', 0);

-- DESIGN TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_mimics', 'attributes', 'lkp_structure_mimics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_zoi_stage', 'attributes', 'lkp_zoi_stage', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_design_status', 'attributes', 'lkp_design_status', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('structure_types', 'attributes', 'structure_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('zoi_types', 'attributes', 'zoi_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_design_sources', 'attributes', 'lkp_design_sources', 0);

-- -- BRAT CIS TABLES
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_base_streampower', 'attributes', 'lkp_brat_base_streampower', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_high_streampower', 'attributes', 'lkp_brat_high_streampower', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_slope', 'attributes', 'lkp_brat_slope', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_dam_density', 'attributes', 'lkp_brat_dam_density', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_vegetation_cis', 'attributes', 'lkp_brat_vegetation_cis', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_combined_cis', 'attributes', 'lkp_brat_combined_cis', 0);

