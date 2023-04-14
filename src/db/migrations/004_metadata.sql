-- Description: Add metadata column to all tables
-- Date: 2023-04-14
ALTER TABLE aoi_features ADD COLUMN metadata TEXT;
ALTER TABLE dam_crests ADD COLUMN metadata TEXT;
ALTER TABLE dams ADD COLUMN metadata TEXT;
ALTER TABLE jams ADD COLUMN metadata TEXT;
ALTER TABLE active_extents ADD metadata TEXT;
ALTER TABLE centerlines ADD COLUMN metadata TEXT;
ALTER TABLE inundation_extents ADD metadata TEXT;
ALTER TABLE valley_bottoms ADD COLUMN metadata TEXT;
ALTER TABLE junctions ADD COLUMN metadata TEXT;
ALTER TABLE geomorphic_units ADD COLUMN metadata TEXT;
ALTER TABLE geomorphic_unit_extents ADD COLUMN metadata TEXT;
ALTER TABLE geomorphic_units_tier3 ADD COLUMN metadata TEXT;
ALTER TABLE cem_phases ADD COLUMN metadata TEXT;
ALTER TABLE vegetation_extents ADD COLUMN metadata TEXT;
ALTER TABLE floodplain_accessibilities ADD COLUMN metadata TEXT;
ALTER TABLE brat_vegetation ADD COLUMN metadata TEXT;
ALTER TABLE brat_cis ADD COLUMN metadata TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN metadata TEXT;
ALTER TABLE channel_unit_points ADD COLUMN metadata TEXT;
ALTER TABLE channel_unit_polygons ADD COLUMN metadata TEXT;
ALTER TABLE structure_types ADD COLUMN metadata TEXT;
ALTER TABLE zoi ADD COLUMN metadata TEXT;
ALTER TABLE complexes ADD COLUMN metadata TEXT;
ALTER TABLE structure_lines ADD COLUMN metadata TEXT;
ALTER TABLE structure_points ADD COLUMN metadata TEXT;
ALTER TABLE pour_points ADD COLUMN metadata TEXT;
ALTER TABLE catchments ADD COLUMN metadata TEXT;