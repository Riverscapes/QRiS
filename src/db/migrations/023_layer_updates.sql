-- Various updates to the layer table
UPDATE layers SET display_name = 'Active Channel Extents' WHERE id = 5;
UPDATE layers SET display_name = 'Active Channel Lines' WHERE id = 7;
UPDATE layers SET display_name = 'Inundation Extents' WHERE id = 8;
UPDATE layers SET display_name = 'Geomporhpic Units Extents' WHERE id = 11;

-- Risk Potential #467
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}, {"machine_code": "risk_type_source", "label": "Type", "type": "list", "lookup": "risk_type_source_points", "allow_custom_values": "true"}]}' WHERE id = 41;
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}, {"machine_code": "risk_type_source", "label": "Type", "type": "list", "lookup": "risk_type_source_lines", "allow_custom_values": "true"}]}' WHERE id = 42;
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}, {"machine_code": "risk_type_source", "label": "Type", "type": "list", "lookup": "risk_type_source_polygons", "allow_custom_values": "true"}]}' WHERE id = 43;

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_points', 'Culvert');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_points', 'Bridge');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_points', 'Diversion');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_lines', 'Road');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_lines', 'Pathway/Trail');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_lines', 'Railroad');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_polygons', 'Infrastructure');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type_source_polygons', 'Crop/Pasture');

-- Geomorphic Units Layers #466
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "geomorphic_unit_type_2_tier", "label": "Type 2 Tier", "type": "list", "lookup": "geomorphic_units_tier2_types"}, {"machine_code": "geomorphic_unit_type", "label": "Type", "type": "list", "lookup": "geomorphic_unit_types"}]}' WHERE id = 11;
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"machine_code": "geomorphic_unit_type_2_tier", "label": "Type 2 Tier", "type": "list", "lookup": "geomorphic_units_tier2_types"}, {"machine_code": "geomorphic_unit_type", "label": "Type", "type": "list", "lookup": "geomorphic_unit_types"}, {"machine_code": "length", "label": "Length", "type": "float"}, {"machine_code": "width", "label": "Width", "type": "float"}, {"machine_code": "depth", "label": "Depth", "type": "float"}]}' WHERE id = 12;

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Pool');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Riffle');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Mid Channel Bar');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Bank Attached Bar');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Glide/Run');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Pond');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Rapid');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('geomorphic_unit_types', 'Chute');

-- Dam Crests Layer #457
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Beaver Dam Building"], "fields": [{"machine_code": "structure_source_id", "label": "Structure Source", "type": "list", "lookup": "structure_source"}, {"machine_code": "dam_state", "label": "Dam State", "type": "list", "lookup": "dam_state"}, {"machine_code": "crest_type", "label": "Crest Type", "type": "list" ,"lookup": "crest_types"}, {"machine_code": "confidence", "label": "Confidence", "type": "list", "lookup": "confidence_levels"}]}' WHERE id = 1;

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('structure_source', 'Natural');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('structure_source', 'Artificial');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('structure_source', 'Unknown');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_state', 'Breached');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_state', 'Intact');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_state', 'Blown Out');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('crest_types', 'Active');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('crest_types', 'Inactive');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('confidence_levels', 'High');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('confidence_levels', 'Medium');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('confidence_levels', 'Low');

-- Vegetation Extents Layer #455
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Vegetation Mapping"], "fields": [{"machine_code": "vegetation_type", "label": "Type", "type": "list", "lookup": "vegetation_types"}, {"machine_code": "vegetation_tier_2_type", "label": "Type 2 Tier", "type": "list", "lookup": "vegetation_tier2_types", "allow_custom_values": "true"}, {"machine_code": "suitability", "label": "Suitability", "type": "list", "lookup": "vegetation_suitability"}]}' WHERE id = 15;

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_types', 'Riparian');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_types', 'Non-Riparian');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_tier2_types', 'Emergent Riparian');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_tier2_types', 'Woody Riparian');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_suitability', 'Unsuitable');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_suitability', 'Barely Suitable');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_suitability', 'Moderately Suitable');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_suitability', 'Suitable');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('vegetation_suitability', 'Preferred');

-- Trim down Structure Type lists # 297
DELETE FROM lookup_list_values WHERE list_name = 'structure_types' AND list_value = 'BDA Large';
DELETE FROM lookup_list_values WHERE list_name = 'structure_types' AND list_value = 'BDA Small';

-- CEM Layer #332
UPDATE layers SET display_name = 'SEM Cluer & Thorne' WHERE id = 14;
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Geomorphic Condition"], "fields": [{"machine_code": "sem_stage", "label": "SEM Stage", "type": "list", "lookup": "sem_stages"}], "menu_items": ["copy_from_valley_bottom"]}' WHERE id = 14;

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '0 Anastomosing');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '1 Sinuous Single Thread');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '2 Channelized');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '3 Degradation');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '4 Degradation and Widening');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '5 Aggradation and Widening');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '6 Quasi Equilibrium');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '7 Laterally Active');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('sem_stages', '8 Anastomosing');
