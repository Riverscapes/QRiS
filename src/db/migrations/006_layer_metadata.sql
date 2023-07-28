-- Description: add field metadata to the layers table to allow for importing feature classes into dce layers
-- Date: 2023-07-24
UPDATE layers SET metadata = '{"fields": {"structure_source_id": {"display_name": "Structure Source", "lookup": "lkp_structure_source"}, "dam_integrity_id": {"display_name": "Dam Integrity", "lookup": "lkp_dam_integrity"}, "beaver_maintenance_id": {"display_name": "Beaver Maintenance", "lookup": "lkp_beaver_maintenance"}}}' WHERE id = 1;
UPDATE layers SET metadata = '{"fields": {"structure_source_id": {"display_name": "Structure Source", "lookup": "lkp_structure_source"}, "dam_integrity_id": {"display_name": "Dam Integrity", "lookup": "lkp_dam_integrity"}, "beaver_maintenance_id": {"display_name": "Beaver Maintenance", "lookup": "lkp_beaver_maintenance"}}}' WHERE id = 3;
UPDATE layers SET metadata = '{"fields": {"structure_source_id": {"display_name": "Structure Source", "lookup": "lkp_structure_source"}, "beaver_maintenance_id": {"display_name": "Beaver Maintenance", "lookup": "lkp_beaver_maintenance"}}}' WHERE id = 4;
UPDATE layers SET metadata = '{"fields": {"type_id": {"display_name": "Thalweg Type", "lookup": "lkp_thalweg_types"}}}' WHERE id = 5;
UPDATE layers SET metadata = '{"fields":{ "type_id": {"display_name": "Extent Type", "lookup": "lkp_active_extent_types"}}}' WHERE id = 6;
UPDATE layers SET metadata = '{"fields": {"type_id": {"display_name": "Extent Type", "lookup": "lkp_inundation_extent_types"}}}' WHERE id = 8; 
UPDATE layers SET metadata = '{"fields": {"type_id": {"display_name": "ZOI Type", "lookup": "zoi_types"}, "stage_id": {"display_name": "ZOI Stage", "lookup": "lkp_zoi_stage"}}}' WHERE id = 19;
UPDATE layers SET metadata = '{"fields": {"structure_type_id": {"display_name": "Structure Type", "lookup": "structure_types"}}}' WHERE id = 21;
UPDATE layers SET metadata = '{"fields": {"structure_type_id": {"display_name": "Structure Type", "lookup": "structure_types"}}}' WHERE id = 22;
UPDATE layers SET metadata = '{"fields": {"unit_type_id": {"display_name": "Unit Type", "lookup": "lkp_channel_unit_types"}, "structure_forced_id": {"display_name": "Structure Forced", "lookup": "lkp_structure_forced"}, "primary_channel_id": {"display_name": "Primary Channel", "lookup": "lkp_primary_channel"},"primary_unit_id":{"display_name": "Primary Unit", "lookup": "lkp_primary_unit"}}}' WHERE id = 23;
UPDATE layers SET metadata = '{"fields": {"unit_type_id": {"display_name": "Unit Type", "lookup": "lkp_channel_unit_types"}, "structure_forced_id": {"display_name": "Structure Forced", "lookup": "lkp_structure_forced"}, "primary_channel_id": {"display_name": "Primary Channel", "lookup": "lkp_primary_channel"},"primary_unit_id":{"display_name": "Primary Unit", "lookup": "lkp_primary_unit"}}}' WHERE id = 24;