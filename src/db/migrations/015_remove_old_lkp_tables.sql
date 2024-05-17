-- Remove old lookup tables
DELETE FROM gpkg_contents WHERE table_name='lkp_structure_mimics';
DELETE FROM gpkg_contents WHERE table_name='lkp_structure_types';
DELETE FROM gpkg_contents WHERE table_name='lkp zoi_stage';
DELETE FROM gpkg_contents WHERE table_name='lkp_zoi_types';