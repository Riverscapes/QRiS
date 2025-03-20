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
INSERT INTO lookups (name) VALUES ('lkp_raster_sources');
INSERT INTO lookups (name) VALUES ('lkp_event_types');
INSERT INTO lookups (name) VALUES ('lkp_raster_types');
INSERT INTO lookups (name) VALUES ('lkp_scratch_vector_types');
INSERT INTO lookups (name) VALUES ('lkp_units');

INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lookups', 'attributes', 'lookups');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_event_types', 'attributes', 'lkp_event_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_raster_types', 'attributes', 'lkp_raster_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_scratch_vector_types', 'attributes', 'lkp_scratch_vector_types');
INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('lkp_units', 'attributes', 'lkp_units');

-- Modify Protocol Library Table
ALTER TABLE protocols ADD COLUMN 'version' TEXT;
UPDATE protocols SET version = '1.0';

-- Update existing protocols in library
UPDATE protocols 
SET description = 'Base LTPBR Layers', 
    metadata = '{"system": {"status": "experimental", "url": "https://lowtechpbr.restoration.usu.edu/", "citation": "Wheaton J.M., Bennett S.N., Bouwes, N., Maestas J.D. and Shahverdian S.M. (Editors). 2019. Low-Tech Process-Based Restoration of Riverscapes: Design Manual. Version 1.0. Utah State University Restoration Consortium. Logan, UT. 286 pp. DOI: 10.13140/RG.2.2.19590.63049/2.", "author": "Nick Weber", "creation_date": "2024-09-01", "updated_date": "2024-09-01"}}' 
WHERE machine_code = 'LTPBR_BASE';

UPDATE protocols 
SET description = 'Design Layers', 
    metadata = '{"system": {"status": "experimental", "url": "https://lowtechpbr.restoration.usu.edu/", "citation": "Wheaton J.M., Bennett S.N., Bouwes, N., Maestas J.D. and Shahverdian S.M. (Editors). 2019. Low-Tech Process-Based Restoration of Riverscapes: Design Manual. Version 1.0. Utah State University Restoration Consortium. Logan, UT. 286 pp. DOI: 10.13140/RG.2.2.19590.63049/2.", "author": "Nick Weber", "creation_date": "2024-09-01", "updated_date": "2024-09-01"}}' 
WHERE machine_code = 'DESIGN';

UPDATE protocols 
SET description = 'AS-Built Layers', 
    metadata = '{"system": {"status": "experimental", "url": "https://lowtechpbr.restoration.usu.edu/", "citation": "Wheaton J.M., Bennett S.N., Bouwes, N., Maestas J.D. and Shahverdian S.M. (Editors). 2019. Low-Tech Process-Based Restoration of Riverscapes: Design Manual. Version 1.0. Utah State University Restoration Consortium. Logan, UT. 286 pp. DOI: 10.13140/RG.2.2.19590.63049/2.", "author": "Nick Weber", "creation_date": "2024-09-01", "updated_date": "2024-09-01"}}' 
WHERE machine_code = 'ASBUILT';

-- Delete protocols if there are no associated layers
DELETE FROM protocols WHERE machine_code = 'LTPBR_BASE' AND NOT EXISTS (SELECT 1 FROM event_layers WHERE layer_id IN (SELECT layer_id FROM method_layers WHERE method_id = 1));
DELETE FROM protocols WHERE machine_code = 'DESIGN' AND NOT EXISTS (SELECT 1 FROM event_layers WHERE layer_id IN (SELECT layer_id FROM method_layers WHERE method_id = 5));
DELETE FROM protocols WHERE machine_code = 'ASBUILT' AND NOT EXISTS (SELECT 1 FROM event_layers WHERE layer_id IN (SELECT layer_id FROM method_layers WHERE method_id = 6));
DELETE FROM protocols WHERE machine_code = 'PLANNING';

-- Clear up old tables
DROP TABLE IF EXISTS 'method_layers';
DROP TABLE IF EXISTS 'methods';
DROP TABLE IF EXISTS 'protocol_methods';

DELETE FROM gpkg_contents WHERE table_name = 'method_layers';
DELETE FROM gpkg_contents WHERE table_name = 'methods';
DELETE FROM gpkg_contents WHERE table_name = 'protocol_methods';