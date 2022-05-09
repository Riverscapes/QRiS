-- LOOKUP TABLES
CREATE TABLE  methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- major question is whether a method is specific to the type of geometry used?
INSERT INTO methods (fid, name,  description) VALUES (1, "RIM", "Riverscape Inundation Mapping");
INSERT INTO methods (fid, name,  description) VALUES (2, "Riverscape Units", "Placeholder name for the streams need space stupidity");
INSERT INTO methods (fid, name,  description) VALUES (3, "Low-Tech Design", "Documentation of a design or as-built low-tech structures");
INSERT INTO methods (fid, name,  description) VALUES (4, "Structural Elements", "Survey of primary structural element types");
INSERT INTO methods (fid, name,  description) VALUES (5, "Geomorphic Units", "In-channel geomorphic unit survey, could be out of channel as well, who fricken knows");
INSERT INTO methods (fid, name,  description) VALUES (6, "Geomorphic Units - Extents", "In-channel geomorphic unit survey, could be out of channel as well, who fricken knows");


CREATE TABLE  metric_sources (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metric_sources (fid, name,  description) VALUES (1, "Calculated", "Calculated from spatial data");
INSERT INTO metric_sources (fid, name,  description) VALUES (2, "Estimated", "Estimated from other sources or evidence");


-- fundamental question is about geometry
CREATE TABLE  layers (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    -- might consider having a display name
    display_name TEXT,
    geom_type TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO layers (fid, name, geom_type, description) VALUES (1, "dam_crests", "lines", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (2, "jam_crests", "lines", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (3, "dams", "points", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (4, "jams", "points", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (5, "thalwegs", "lines", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (6, "riverscape_units", "polygons", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (7, "centerlines", "lines", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (8, "wetted_channel", "polygons", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (9, "valley_bottoms", "polygons", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (10, "junctions", "points", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (11, "geomorphic_unit_extents", "polygons", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (12, "geomorphic_units", "points", "");
INSERT INTO layers (fid, name, geom_type, description) VALUES (13, "cem_phases", "polygons", "");

CREATE TABLE  method_layers (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    layer_id INTEGER REFERENCES layers(fid) ON DELETE CASCADE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO method_layers (fid, method_id, layer_id) VALUES (1, 1, 1);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (2, 1, 5);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (3, 1, 8);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (4, 2, 6);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (5, 2, 9);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (6, 4, 3);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (7, 4, 4);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (8, 5, 12);
INSERT INTO method_layers (fid, method_id, layer_id) VALUES (9, 6, 11);


-- NON-SPATIAL TABLES
CREATE TABLE projects (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    -- additional attributes
    -- created_by could be optional or filled through a variable in QGIS    
    created_by TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Could consider using epoch as an attribute of a survey. Epochs could still be defined as a range of dates.

CREATE TABLE assessments (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(fid) ON DELETE CASCADE,
    -- should epoch have a lookup table of fixed values [historic, current, future]
    -- this concept needs to be further explored. How do we name it
    -- 'name' could switch back to 'epoch' if the table becomes 'assessments'
    epoch TEXT,
    description TEXT,
    -- should the assessment date be a range?
    -- how to deal with historic dates or date with less precision
    -- Could these dates actually be a range of years with specific dates being in the assessments_methods
    start_date DATE,
    end_date DATE,
    -- not sure if we want created_by in here or not
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessment_methods (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    -- I don't like this table name. Could we call it surveys
    method_id INTEGER REFERENCES methods(fid) ON DELETE CASCADE,
    -- not sure if platform is necessary here [desktop, field]
    platform TEXT,
    description TEXT,
    date DATE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE  bases (
    -- this table name is horid. try: contexts, evidences, base_rasters
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    name TEXT,
    path TEXT,
    -- type will likely be populated from a lookup. e.g., imagery, dem, lidar, etc....
    type TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE  masks (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(fid) ON DELETE CASCADE,
    name TEXT,
    type TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE mask_features ADD COLUMN mask_id INTEGER REFERENCES masks(fid) ON DELETE CASCADE;
-- type should probably have a lookup table
ALTER TABLE mask_features ADD COLUMN type TEXT;
ALTER TABLE mask_features ADD COLUMN position INTEGER;
ALTER TABLE mask_features ADD COLUMN description TEXT;


CREATE TABLE  calculations (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE  metrics (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculations(fid) ON DELETE CASCADE,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE  metric_values (
    fid INTEGER PRIMARY KEY AUTOINCREMENT,
    mask_feature_id INTEGER REFERENCES mask_features(fid) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES metrics(fid) ON DELETE CASCADE,
    assessment_id INTEGER REFERENCES assessments(fid) ON DELETE CASCADE,
    metric_source_id INTEGER REFERENCES metric_sources(fid) ON DELETE CASCADE,
    value NUMERIC,
    Uncertainty NUMERIC,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);
