-- Add Version field to all Layers, set to 1.0
ALTER TABLE layers ADD COLUMN version TEXT;
UPDATE layers SET version = '1.0';

-- Remove unused lookup tables
DROP TABLE IF EXISTS 'lkp_mask_types';
DELETE FROM gpkg_contents WHERE table_name = 'lkp_mask_types';
DROP TABLE IF EXISTS 'lkp_beaver_maintenance';
DELETE FROM gpkg_contents WHERE table_name = 'lkp_beaver_maintenance';
DROP TABLE IF EXISTS 'lkp_dam_integrity';
DELETE FROM gpkg_contents WHERE table_name = 'lkp_dam_integrity';
DROP TABLE IF EXISTS 'lkp_design_status';
DELETE FROM gpkg_contents WHERE table_name = 'lkp_design_status';
DROP TABLE IF EXISTS 'lkp_context_layer_types';
DELETE FROM gpkg_contents WHERE table_name = 'lkp_context_layer_types';

-- Drop old Lookup Values table
DROP TABLE IF EXISTS 'lookup_list_values';
DELETE FROM gpkg_contents WHERE table_name = 'lookup_list_values';

-- Add Raster Source Lookup Table
CREATE TABLE lkp_raster_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP);

INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_raster_sources', 'attributes', 'lkp_raster_sources');

INSERT INTO lkp_raster_sources (name) VALUES ('Riverscapes Project');
INSERT INTO lkp_raster_sources (name) VALUES ('Satellite');
INSERT INTO lkp_raster_sources (name) VALUES ('Drone');
INSERT INTO lkp_raster_sources (name) VALUES ('DroneDeploy');
INSERT INTO lkp_raster_sources (name) VALUES ('Pleadies-Neo Satellite');
INSERT INTO lkp_raster_sources (name) VALUES ('Derived');

-- New Table for Lookups
CREATE TABLE lookups (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL);

INSERT INTO lookups (name) VALUES ('lkp_platform');
INSERT INTO lookups (name) VALUES ('lkp_representation');
INSERT INTO lookups (name) VALUES ('lkp_design_sources');
INSERT INTO lookups (name) VALUES ('lkp_event_types');
INSERT INTO lookups (name) VALUES ('lkp_raster_types');
INSERT INTO lookups (name) VALUES ('lkp_scratch_vector_types');
INSERT INTO lookups (name) VALUES ('lkp_units');

INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lookups', 'attributes', 'lookups');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_event_types', 'attributes', 'lkp_event_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_raster_types', 'attributes', 'lkp_raster_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_scratch_vector_types', 'attributes', 'lkp_scratch_vector_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_units', 'attributes', 'lkp_units');

-- Find all unused layers and delete them
DELETE FROM layers WHERE id NOT IN (SELECT layer_id FROM event_layers);

-- Here we will modify the layers table to use the new schema
CREATE TABLE protocol_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_id INTEGER NOT NULL,
    layer_id INTEGER NOT NULL,
    FOREIGN KEY(protocol_id) REFERENCES protocols(id),
    FOREIGN KEY(layer_id) REFERENCES layers(id));

INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('protocol_layers', 'attributes', 'protocol_layers');

-- Clear up old tables
DROP TABLE IF EXISTS 'method_layers';
DROP TABLE IF EXISTS 'methods';
DROP TABLE IF EXISTS 'protocol_methods';

DELETE FROM gpkg_contents WHERE table_name = 'method_layers';
DELETE FROM gpkg_contents WHERE table_name = 'methods';
DELETE FROM gpkg_contents WHERE table_name = 'protocol_methods';

ALTER TABLE protocols ADD COLUMN 'version' TEXT;
UPDATE protocols SET version = '1.0';