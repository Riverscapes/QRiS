-- Unlock the Database
PRAGMA foreign_keys=OFF;

-- Find all unused layers and delete them
DELETE FROM layers WHERE id NOT IN (SELECT layer_id FROM event_layers);

-- Rebuild the layers table without the constraint on the fc_name column
CREATE TEMP TABLE layers_temp AS SELECT * FROM layers;
DROP TABLE layers;

CREATE TABLE layers (
    id INTEGER PRIMARY KEY,
    fc_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    qml TEXT,
    is_lookup BOOLEAN,
    geom_type TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, description, metadata, created_on)
SELECT id, fc_name, display_name, qml, is_lookup, geom_type, description, metadata, created_on FROM layers_temp;
DROP TABLE layers_temp;

-- Add Version field to all Layers, set to 1.0
ALTER TABLE layers ADD COLUMN version TEXT;
UPDATE layers SET version = '1.0';

-- Update the layers schema to the updated version
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Beaver Dam Building"], "fields": [{"id": "structure_source_id", "type": "list", "label": "Structure Source", "required": false, "allow_custom_values": false, "values": ["Artificial", "Natural", "Unknown"]}, {"id": "dam_state", "type": "list", "label": "Dam State", "required": false, "allow_custom_values": false, "values": ["Blown Out", "Breached", "Intact"]}, {"id": "crest_type", "type": "list", "label": "Crest Type", "required": false, "allow_custom_values": false, "values": ["Active", "Inactive"]}, {"id": "confidence", "type": "list", "label": "Confidence", "required": false, "allow_custom_values": false, "values": ["High", "Medium", "Low"]}]}' WHERE fc_name = 'dam_crests';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": []}' WHERE fc_name = 'active_channel';
UPDATE layers SET metadata = '{"menu_items": ["copy_from_valley_bottom"], "hierarchy": ["Observations", "Geomorphic Mapping", "Floodplain"], "fields": [{"id": "type_id", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Active", "Inactive"]}]}' WHERE fc_name = 'active_extents';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"id": "type_id", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Primary", "Non-Primary"]}, {"id": "description", "type": "list", "label": "Description", "required": false, "allow_custom_values": false, "values": ["Centerline", "Thalweg"], "default_value": "Centerline"}]}' WHERE fc_name = 'centerlines';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Hydraulic Mapping"], "fields": [{"id": "type_id", "type": "list", "label": "Extent Type", "required": false, "allow_custom_values": false, "values": ["Free Flowing", "Overflow", "Ponded"]}]}' WHERE fc_name = 'inundation_extents';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"id": "junction_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Channel Head", "Confluence (Anabranch)", "Confluence (Tributary)", "Diffluence"]}]}' WHERE fc_name = 'channel_junctions';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"id": "geomorphic_unit_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Bank Attached Bar", "Chute", "Glide/Run", "Mid Channel Bar", "Pond", "Pool", "Rapid", "Riffle"]}, {"id": "geomorphic_unit_type_2_tier", "type": "list", "label": "Type 2 Tier", "required": false, "allow_custom_values": false, "values": ["Bowl", "Mound", "Plane", "Saddle", "Trough"]}]}' WHERE fc_name = 'geomorphic_unit_extents';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Geomorphic Mapping", "Channel"], "fields": [{"id": "geomorphic_unit_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Bank Attached Bar", "Chute", "Glide/Run", "Mid Channel Bar", "Pond", "Pool", "Rapid", "Riffle"]}, {"id": "geomorphic_unit_type_2_tier", "type": "list", "label": "Type 2 Tier", "required": false, "allow_custom_values": false, "values": ["Bowl", "Mound", "Plane", "Saddle", "Trough"]}, {"id": "length", "type": "float", "label": "Length", "required": false, "allow_custom_values": false}, {"id": "width", "type": "float", "label": "Width", "required": false, "allow_custom_values": false}, {"id": "depth", "type": "float", "label": "Depth", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'geomorphic_units';
UPDATE layers SET metadata = '{"menu_items": ["copy_from_valley_bottom"], "hierarchy": ["Assessments", "Geomorphic Condition"], "fields": [{"id": "sem_stage", "type": "list", "label": "SEM Stage", "required": false, "allow_custom_values": false, "values": ["0 Anastomosing", "1 Sinuous Single Thread", "2 Channelized", "3 Degradation", "4 Degradation and Widening", "5 Aggradation and Widening", "6 Quasi Equilibrium", "7 Laterally Active", "8 Anastomosing"]}]}' WHERE fc_name = 'cem_phases';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Vegetation Mapping"], "fields": [{"id": "vegetation_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Riparian", "Non-Riparian"]}, {"id": "vegetation_tier_2_type", "type": "list", "label": "Type 2 Tier", "required": false, "allow_custom_values": false, "values": ["Emergent Riparian", "Woody Riparian"]}, {"id": "suitability", "type": "list", "label": "Brat Suitability", "required": false, "allow_custom_values": false, "values": ["Preferred", "Suitable", "Moderately Suitable", "Barely Suitable", "Unsuitable"]}]}' WHERE fc_name = 'vegetation_extents';
UPDATE layers SET metadata = '{"menu_items": ["import_photos"], "hierarchy": ["Observations", "Other"], "fields": [{"id": "photo_path", "type": "attachment", "label": "Photo Path", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'observation_points_dce';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Other"], "fields": []}' WHERE fc_name = 'observation_lines_dce';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Other"], "fields": []}' WHERE fc_name = 'observation_polygons_dce';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"id": "structural_element_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Dam", "Dam Complex", "Jam", "Jam Complex", "Other", "Root Mass"]}, {"id": "structure_count", "type": "integer", "label": "Structure Count", "required": false, "allow_custom_values": false, "default_value": "1", "visibility_values": []}, {"id": "length", "type": "float", "label": "Length", "required": false, "allow_custom_values": false, "visibility_values": []}, {"id": "width", "type": "float", "label": "Width", "required": false, "allow_custom_values": false, "visibility_values": []}, {"id": "height", "type": "float", "label": "Height", "required": false, "allow_custom_values": false, "visibility_values": []}, {"id": "large_wood_count", "type": "integer", "label": "Large Wood Count", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'structural_elements_points';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"id": "structural_element_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Dam"]}]}' WHERE fc_name = 'structural_elements_lines';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Structural Elements"], "fields": [{"id": "structural_element_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Jam"]}, {"id": "large_wood_count", "type": "integer", "label": "Large Wood Count", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'structural_elements_areas';
UPDATE layers SET metadata = '{"menu_items": ["copy_from_valley_bottom"], "hierarchy": ["Assessments"], "fields": []}' WHERE fc_name = 'recovery_potential';
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"id": "risk_type", "type": "list", "label": "Risk", "required": false, "allow_custom_values": false, "values": ["High", "Medium", "Low"]}, {"id": "risk_type_source", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Bridge", "Culvert", "Diversion"]}]}' WHERE fc_name = 'risk_potential_points';
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"id": "risk_type", "type": "list", "label": "Risk", "required": false, "allow_custom_values": false, "values": ["High", "Medium", "Low"]}, {"id": "risk_type_source", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Pathway/Trail", "Railroad", "Road"]}]}' WHERE fc_name = 'risk_potential_lines';
UPDATE layers SET metadata = '{"hierarchy": ["Assessments", "Risk Potential"], "fields": [{"id": "risk_type", "type": "list", "label": "Risk", "required": false, "allow_custom_values": false, "values": ["High", "Medium", "Low"]}, {"id": "risk_type_source", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["Crop/Pasture", "Infrastructure"]}]}' WHERE fc_name = 'risk_potential_polygons';
-- beaver census
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Beaver Activity"], "fields": [{"id": "dam_cer", "type": "list", "label": "Dam CER", "required": false, "allow_custom_values": false, "values": ["high", "medium", "low"]}, {"id": "dam_type", "type": "list", "label": "Dam Type", "required": false, "allow_custom_values": false, "values": ["active_dam", "inactive_dam", "relic"]}, {"id": "type_cer", "type": "list", "label": "Type CER", "required": false, "allow_custom_values": false, "values": ["high", "medium", "low"]}]}' WHERE fc_name = 'beaver_dam';
UPDATE layers SET metadata = '{"hierarchy": ["Observations", "Beaver Activity"], "fields": [{"id": "sign_type", "type": "list", "label": "Type", "required": false, "allow_custom_values": false, "values": ["bank_den", "bank_lodge", "canal", "chew_stick", "clipped_vegetation", "felled_tree", "food_cache", "harvested_branches", "other", "pond_excavation", "pond_lodge", "scat", "scent_mound", "set_of_tracks", "skid_trail", "slide"]}]}' WHERE fc_name = 'beaver_sign';
-- design
UPDATE layers SET metadata = '{"hierarchy": ["Structures"], "fields": []}' WHERE fc_name = 'complexes';
UPDATE layers SET metadata = '{"hierarchy": ["Structures"], "fields": [{"id": "structure_type", "type": "list", "label": "Structure Type", "required": false, "allow_custom_values": false, "values": ["ALS", "ALS - Bank Attached", "ALS - Bank Blaster", "ALS - Channel Spanning", "ALS - Rhino", "BDA", "BDA Postless", "Bag Plugs", "Fell Tree", "Floodplain BDA", "Floodplain LWD", "Full Tree", "Grip Hoist Tree", "Headcut Treatment", "Leaky Dam", "One Rock Dam", "PALS", "PALS - Bank Attached", "PALS - Bank Blaster", "PALS - Channel Spanning", "PALS - Constriction Jet", "PALS - Left Bank Attached", "PALS - Mid Channel", "PALS - Rhino", "PALS - Right Bank Attached", "Post and Brush Plug", "Postline Wicker Weave", "Primary BDA", "Rhino", "Secondary BDA", "Sedge Plugs", "Spreaders", "Strategic Felling", "Tight PALS (BDA without sod)", "Tree Dam", "Tree Plug", "Vanes", "Wicker Weirs", "Wood Jam", "Zuni Bowl"]}]}' WHERE fc_name = 'structure_points';
UPDATE layers SET metadata = '{"hierarchy": ["Structures"], "fields": [{"id": "structure_type", "type": "list", "label": "Structure Type", "required": false, "allow_custom_values": false, "values": ["ALS", "ALS - Bank Attached", "ALS - Bank Blaster", "ALS - Channel Spanning", "ALS - Rhino", "BDA", "BDA Postless", "Bag Plugs", "Fell Tree", "Floodplain BDA", "Floodplain LWD", "Full Tree", "Grip Hoist Tree", "Headcut Treatment", "Leaky Dam", "One Rock Dam", "PALS", "PALS - Bank Attached", "PALS - Bank Blaster", "PALS - Channel Spanning", "PALS - Constriction Jet", "PALS - Left Bank Attached", "PALS - Mid Channel", "PALS - Rhino", "PALS - Right Bank Attached", "Post and Brush Plug", "Postline Wicker Weave", "Primary BDA", "Rhino", "Secondary BDA", "Sedge Plugs", "Spreaders", "Strategic Felling", "Tight PALS (BDA without sod)", "Tree Dam", "Tree Plug", "Vanes", "Wicker Weirs", "Wood Jam", "Zuni Bowl"]}]}' WHERE fc_name = 'structure_lines';
UPDATE layers SET metadata = '{"hierarchy": [], "fields": [{"id": "zoi_type", "type": "list", "label": "ZOI Type", "required": false, "allow_custom_values": false, "values": ["Complex: Headcut Arrest", "Complex: Increase Channel Complexity", "Complex: Increase Floodplain Connectivity", "Complex: Lateral Channel Migration", "Complex: Overbank Flow Dispersal", "Complex: Pond/Wetland Creation", "Complex: Riparian/Wetland Expansion", "Complex: Side-Channel Connection", "Complex: Widening and Aggradation", "Structure: Geomorphic - Deposition in upstream backwater", "Structure: Geomorphic - Deposition of bar", "Structure: Geomorphic - Deposition overbank", "Structure: Geomorphic - Erode Bank", "Structure: Geomorphic - Erosion from convergent jet", "Structure: Geomorphic - Erosion from plunge", "Structure: Geomorphic - Erosion from return flow headcut", "Structure: Geomorphic - Erosion of bar edge", "Structure: Hydraulic - Constriction Jet", "Structure: Hydraulic - Divergent Flow", "Structure: Hydraulic - Eddy", "Structure: Hydraulic - Overflow", "Structure: Hydraulic - Ponding Flow", "Structure: Hydraulic - Shunting Flow", "Structure: Hydraulic - Splitting Flow", "Structure: Scout Pool Formation"]}, {"id": "zoi_stage", "type": "list", "label": "Stage", "required": false, "allow_custom_values": false, "values": ["Baseflow", "Typical Flood", "Large Flood", "Other"]}]}' WHERE fc_name = 'zoi';
UPDATE layers SET metadata = '{"menu_items": ["import_photos"], "hierarchy": ["Observations"], "fields": [{"id": "observation_point_type", "type": "list", "label": "Observation Type", "required": false, "allow_custom_values": false, "values": ["Building Materials", "Caution", "Design Consideration", "Logistics", "Riverscape Feature", "Photo Observation", "Other"]}, {"id": "photo_path", "type": "attachment", "label": "Photo Path", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'observation_points';
UPDATE layers SET metadata = '{"hierarchy": ["Observations"], "fields": [{"id": "observation_polygon_type", "type": "list", "label": "Observation Type", "required": false, "allow_custom_values": false, "values": ["Caution", "Logistics", "Riverscape Feature", "Road", "Other"]}]}' WHERE fc_name = 'observation_polygons';
UPDATE layers SET metadata = '{"hierarchy": ["Observations"], "fields": [{"id": "observation_line_type", "type": "list", "label": "Observation Type", "required": false, "allow_custom_values": false, "values": ["Building Materials", "Caution", "Infrastructure", "Logistics", "Other"]}]}' WHERE fc_name = 'observation_lines';
-- asbuilt
UPDATE layers SET metadata = '{"menu_items": ["import_photos"], "hierarchy": ["Observations"], "fields": [{"id": "observation_point_type", "type": "list", "label": "Observation Type", "required": false, "allow_custom_values": false, "values": ["Building Materials", "Caution", "Design Consideration", "Logistics", "Riverscape Feature", "Photo Observation", "Other"]}, {"id": "photo_path", "type": "attachment", "label": "Photo Path", "required": false, "allow_custom_values": false}]}' WHERE fc_name = 'observation_points_asbuilt';
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, description, metadata) VALUES (46, 'structure_points', 'Structure Points', 'structure_points.qml', 0, 'Point', 'Structure Points Layer', '{"hierarchy": ["Structures"], "fields": [{"id": "structure_type", "type": "list", "label": "Structure Type", "required": false, "allow_custom_values": false, "values": ["ALS", "ALS - Bank Attached", "ALS - Bank Blaster", "ALS - Channel Spanning", "ALS - Rhino", "BDA", "BDA Postless", "Bag Plugs", "Fell Tree", "Floodplain BDA", "Floodplain LWD", "Full Tree", "Grip Hoist Tree", "Headcut Treatment", "Leaky Dam", "One Rock Dam", "PALS", "PALS - Bank Attached", "PALS - Bank Blaster", "PALS - Channel Spanning", "PALS - Constriction Jet", "PALS - Left Bank Attached", "PALS - Mid Channel", "PALS - Rhino", "PALS - Right Bank Attached", "Post and Brush Plug", "Postline Wicker Weave", "Primary BDA", "Rhino", "Secondary BDA", "Sedge Plugs", "Spreaders", "Strategic Felling", "Tight PALS (BDA without sod)", "Tree Dam", "Tree Plug", "Vanes", "Wicker Weirs", "Wood Jam", "Zuni Bowl"]}]}');
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, description, metadata) VALUES (47, 'structure_lines', 'Structure Lines', 'structure_lines.qml', 0, 'Linestring', 'Structure Lines Layer', '{"hierarchy": ["Structures"], "fields": [{"id": "structure_type", "type": "list", "label": "Structure Type", "required": false, "allow_custom_values": false, "values": ["ALS", "ALS - Bank Attached", "ALS - Bank Blaster", "ALS - Channel Spanning", "ALS - Rhino", "BDA", "BDA Postless", "Bag Plugs", "Fell Tree", "Floodplain BDA", "Floodplain LWD", "Full Tree", "Grip Hoist Tree", "Headcut Treatment", "Leaky Dam", "One Rock Dam", "PALS", "PALS - Bank Attached", "PALS - Bank Blaster", "PALS - Channel Spanning", "PALS - Constriction Jet", "PALS - Left Bank Attached", "PALS - Mid Channel", "PALS - Rhino", "PALS - Right Bank Attached", "Post and Brush Plug", "Postline Wicker Weave", "Primary BDA", "Rhino", "Secondary BDA", "Sedge Plugs", "Spreaders", "Strategic Felling", "Tight PALS (BDA without sod)", "Tree Dam", "Tree Plug", "Vanes", "Wicker Weirs", "Wood Jam", "Zuni Bowl"]}]}');
UPDATE event_layers SET layer_id = 46 WHERE layer_id = 21 AND event_id = (SELECT id from events WHERE event_type_id = 3);
UPDATE event_layers SET layer_id = 47 WHERE layer_id = 22 AND event_id = (SELECT id from events WHERE event_type_id = 3);

-- Create a new protocol layers table
CREATE TABLE protocol_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_id INTEGER NOT NULL,
    layer_id INTEGER NOT NULL,
    FOREIGN KEY(protocol_id) REFERENCES protocols(id),
    FOREIGN KEY(layer_id) REFERENCES layers(id));

INSERT INTO gpkg_contents (table_name, data_type, identifier) VALUES ('protocol_layers', 'attributes', 'protocol_layers');

-- Insert protocol layers only if they exist
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'dam_crests' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'dam_crests');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'active_channel' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'active_channel');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'active_extents' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'active_extents');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'centerlines' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'centerlines');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'inundation_extents' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'inundation_extents');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'channel_junctions' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'channel_junctions');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'geomorphic_unit_extents' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'geomorphic_unit_extents');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'geomorphic_units' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'geomorphic_units');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'cem_phases' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'cem_phases');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'vegetation_extents' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'vegetation_extents');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'observation_points_dce' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'observation_points_dce');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'observation_lines_dce' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'observation_lines_dce');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'observation_polygons_dce' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'observation_polygons_dce');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'structural_elements_points' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structural_elements_points');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'structural_elements_lines' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structural_elements_lines');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'structural_elements_areas' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structural_elements_areas');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'recovery_potential' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'recovery_potential');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'risk_potential_points' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'risk_potential_points');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'risk_potential_lines' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'risk_potential_lines');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'risk_potential_polygons' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'risk_potential_polygons');
INSERT INTO protocol_layers (protocol_id, layer_id)
-- brat cis
SELECT 1, id FROM layers WHERE fc_name = 'brat_cis' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'brat_cis');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'brat_cis_reaches' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'brat_cis_reaches');
-- brat census
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'beaver_dam' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'beaver_dam');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 1, id FROM layers WHERE fc_name = 'beaver_sign' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'beaver_sign');
-- design
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 4, id FROM layers WHERE fc_name = 'zoi' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'zoi');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 4, id FROM layers WHERE fc_name = 'complexes' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'complexes');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 4, 21 FROM layers WHERE fc_name = 'structure_points' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structure_points') AND EXISTS (SELECT 1 from events WHERE event_type_id = 2);
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 4, 22 FROM layers WHERE fc_name = 'structure_lines' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structure_lines') AND EXISTS (SELECT 1 from events WHERE event_type_id = 2);
-- asbuilt
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 5, id FROM layers WHERE fc_name = 'observation_points_asbuilt' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'observation_points_asbuilt');
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 5, 46 FROM layers WHERE fc_name = 'structure_points' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structure_points') AND EXISTS (SELECT 1 from events WHERE event_type_id = 3);
INSERT INTO protocol_layers (protocol_id, layer_id)
SELECT 5, 47 FROM layers WHERE fc_name = 'structure_lines' AND EXISTS (SELECT 1 FROM layers WHERE fc_name = 'structure_lines') AND EXISTS (SELECT 1 from events WHERE event_type_id = 3);

-- Find all unused layers and delete them
DELETE FROM layers WHERE id NOT IN (SELECT layer_id FROM event_layers);

PRAGMA foreign_keys=ON;