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

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (133, 'lkp_units', 'Unit Types', 'NoGeometry', 1, 'none.qml', NULL);

INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (1, 'Meters', 'm', NULL, NULL, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (2, 'Square Meters', '㎡', NULL, NULL, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (3, 'Cubic Meters', 'm³', NULL, NULL, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (4, 'Feet', 'ft', 0.3048, 1, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (5, 'Square Feet', 'sqft', 0.092903, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (6, 'Cubic Feet', 'ft³', 0.0283168, 3, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (7, 'Hectares', 'ha', 10000, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (8, 'Acres', 'ac', 4046.86, 2, 'area');

ALTER TABLE metric_values ADD COLUMN unit_id INTEGER REFERENCES lkp_units(id);
--ALTER TABLE metric_values ADD CONSTRAINT pk_metric_values PRIMARY KEY (analysis_id, event_id, mask_feature_id, metric_id);

ALTER TABLE calculations ADD COLUMN metric_function TEXT;

INSERT INTO calculations (id, name, metric_function) VALUES (1, 'count', 'count');
INSERT INTO calculations (id, name, metric_function) VALUES (2, 'length', 'length');
INSERT INTO calculations (id, name, metric_function) VALUES (3, 'area', 'area');
INSERT INTO calculations (id, name, metric_function) VALUES (4, 'sinuosity', 'sinuosity');
INSERT INTO calculations (id, name, metric_function) VALUES (5, 'gradient', 'gradient');

ALTER TABLE metrics ADD COLUMN unit_id INTEGER REFERENCES lkp_units(id);
ALTER TABLE metrics ADD COLUMN metric_params TEXT;

UPDATE metrics SET calculation_id=1, metadata='{"min_value": 0}', metric_params='{"layers": ["dams","jams"]}' WHERE id = 1;
UPDATE metrics SET name='Percent Active Floodplain', metadata='{"min_value": 0, "max_value": 100, "tolerance": 0.25}' WHERE id = 2;
UPDATE metrics SET calculation_id=5, name='Centerline Gradient', metadata='{"precision": 4, "tolerance": 0.1}', metric_params='{"layers": ["profile_centerlines"], "rasters": ["Digital Elevation Model (DEM)"]}' WHERE id = 3;
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (4, 2, 'Dam Crest Length', 1, 1, '{"layers": ["dam_crests"]}', '{"min_value": 0, "max_value": 10000, "precision": 2, "tolerance": 0.1}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (5, 3, 'Valley Bottom Area', 1, 2, '{"layers": ["valley_bottoms"]}', NULL);
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (6, 4, 'Centelrine Sinuosity', 1,  NULL, '{"layers": ["profile_centerlines"]}', '{"min_value": 1, "precision": 4, "tolerance": 0.1}');
