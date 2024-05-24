-- This script adds additional raster types to the lkp_raster_types table
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (7, 'Slope Raster','Shared/slope.qml');
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (8, 'Geomorphic Change Detection (GCD)',NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (9, 'Orthomosaic', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (10, 'Satellite', NULL);
