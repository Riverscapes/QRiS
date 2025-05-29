-- Unlock the Database
PRAGMA foreign_keys=OFF;

-- Rebuild the metrics table without the unique constraint on the name column
CREATE TEMP TABLE metrics_temp AS SELECT * FROM metrics;
DROP TABLE metrics;

CREATE TABLE "metrics" (
	"id"	INTEGER,
	"calculation_id"	INTEGER,
	"default_level_id"	INTEGER,
	"unit_id"	INTEGER,
	"name"	TEXT NOT NULL,
	"description"	TEXT,
	"definition_url"	TEXT,
	"metadata"	TEXT,
	"created_on"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"metric_params"	TEXT,
	"machine_name"	TEXT NOT NULL DEFAULT '',
	"version"	TEXT NOT NULL DEFAULT 1.0,
	"protocol_id"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("calculation_id") REFERENCES "calculations"("id"),
	FOREIGN KEY("default_level_id") REFERENCES "metric_levels"("id"),
	FOREIGN KEY("unit_id") REFERENCES "lkp_units"("id")
);

INSERT INTO metrics (id, calculation_id, default_level_id, unit_id, name, description, definition_url, metadata, metric_params, machine_name, version)
    SELECT id, calculation_id, default_level_id, unit_id, name, description, definition_url, metadata, metric_params, machine_name, version
    FROM metrics_temp;

UPDATE metrics SET protocol_id = (SELECT id FROM protocols WHERE machine_code = 'LTPBR_BASE');
UPDATE metrics SET version = '1.0';

DELETE FROM metrics WHERE protocol_id is NULL;

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "structural_elements_points", "attribute_filter": {"field_id_ref": "structural_element_type", "values": ["Dam", "Dam Complex"]}, "count_fields": [{"field_id_ref": "structure_count"}], "usage": "Numerator"}]}'
WHERE machine_name = 'dam_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "centerlines"}]}'
WHERE machine_name = 'active_channel_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Channel Head"]}}]}'
WHERE machine_name = 'channel_head_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Channel Head"]}}]}'
WHERE machine_name = 'channel_head_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "centerlines", "attribute_filter": {"field_id_ref": "type_id", "values": ["Primary"]}}]}'
WHERE machine_name = 'channel_sinuosity';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Confluence (Anabranch)", "Confluence (Tributary)"]}}]}'
WHERE machine_name = 'confluence_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Confluence (Anabranch)", "Confluence (Tributary)"]}}]}'
WHERE machine_name = 'confluence_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "structural_elements_points", "attribute_filter": {"field_id_ref": "structure_type", "values": ["Dam", "Dam Complex"]}, "count_fields": [{"field_id_ref": "structure_count"}]}]}'
WHERE machine_name = 'dam_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Diffluence"]}}]}'
WHERE machine_name = 'diffluence_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "channel_junctions", "attribute_filter": {"field_id_ref": "junction_type", "values": ["Diffluence"]}}]}'
WHERE machine_name = 'diffluence_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "centerlines"}]}'
WHERE machine_name = 'flow_length';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Free Flowing"]}}]}'
WHERE machine_name = 'free_flowing_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents"}]}'
WHERE machine_name = 'inundated_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "active_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Active"]}, "usage": "Numerator"}]}'
WHERE machine_name = 'proportion_active';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "structural_elements_areas", "attribute_filter": {"field_id_ref": "structural_element_type", "values": ["Jam"]}}]}'
WHERE machine_name = 'jam_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "structural_elements_points", "attribute_filter": {"field_id_ref": "structural_element_type", "values": ["Jam", "Jam Complex"]}, "count_fields": [{"field_id_ref": "structure_count"}]}, {"layer_id_ref": "structural_elements_areas", "attribute_filter": {"field_id_ref": "structural_element_type", "values": ["Jam"]}}]}'
WHERE machine_name = 'jam_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "structural_elements_points", "attribute_filter": {"field_id_ref": "Type", "values": ["Jam", "Jam Complex"]}, "count_fields": [{"field_id_ref": "structure_count"}]}, {"layer_id_ref": "structural_elements_areas", "attribute_filter": {"field_id_ref": "Type", "values": ["Jam"]}}]}'
WHERE machine_name = 'jam_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Mid Channel Bar"]}}]}'
WHERE machine_name = 'mid_channel_bar_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Mid Channel Bar"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Mid Channel Bar"]}}]}'
WHERE machine_name = 'mid_channel_bar_count';

UPDATE metrics SET machine_name = 'mid_channel_bar_density'
WHERE machine_name = 'bar_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Mid Channel Bar"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Mid Channel Bar"]}}]}'
WHERE machine_name = 'mid_channel_bar_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Overflow"]}}]}'
WHERE machine_name = 'overflow_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Free Flowing"]}, "usage": "Numerator"}, {"layer_id_ref": "inundation_extents", "usage": "Denominator"}]}'
WHERE machine_name = 'percent_free_flowing';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "usage": "Numerator"}]}'
WHERE machine_name = 'percent_inundated';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Overflow"]}, "usage": "Numerator"}, {"layer_id_ref": "inundation_extents", "usage": "Denominator"}]}'
WHERE machine_name = 'percent_overflow';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Ponded"]}, "usage": "Numerator"}, {"layer_id_ref": "inundation_extents", "usage": "Denominator"}]}'
WHERE machine_name = 'percent_ponded';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "vegetation_extents", "attribute_filter": {"field_id_ref": "vegetation_type", "values": ["Riparian"]}, "usage": "Numerator"}]}'
WHERE machine_name = 'percent_riparian_vegetation';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Pool", "Pond", "Chute"]}}]}'
WHERE machine_name = 'pool_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Pool", "Pond", "Chute"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Pool", "Pond", "Chute"]}}]}'
WHERE machine_name = 'pool_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Pool", "Pond", "Chute"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Pool", "Pond", "Chute"]}}]}'
WHERE machine_name = 'pool_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "inundation_extents", "attribute_filter": {"field_id_ref": "type_id", "values": ["Ponded"]}}]}'
WHERE machine_name = 'ponded_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3, "maximum_value": 1000000}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "centerlines", "attribute_filter": {"field_id_ref": "type_id", "values": ["Primary"]}}]}'
WHERE machine_name = 'primary_channel_length';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "centerlines"}]}'
WHERE machine_name = 'relative_flow_length';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Riffle"]}}]}'
WHERE machine_name = 'riffle_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 1}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Riffle"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Riffle"]}}]}'
WHERE machine_name = 'riffle_count';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "normalization"}], "dce_layers": [{"layer_id_ref": "geomorphic_units", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Riffle"]}}, {"layer_id_ref": "geomorphic_unit_extents", "attribute_filter": {"field_id_ref": "geomorphic_unit_type", "values": ["Riffle"]}}]}'
WHERE machine_name = 'riffle_density';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "valley_bottom", "usage": "metric_layer"}]}'
WHERE machine_name = 'riverscape_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"inputs": [{"input_ref": "centerline", "usage": "metric_layer"}]}'
WHERE machine_name = 'riverscape_length';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "centerlines", "attribute_filter": {"field_id_ref": "type_id", "values": ["Non-Primary"]}}]}'
WHERE machine_name = 'secondary_channel_length';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["0 Anastomosing"]}}]}'
WHERE machine_name = 'stage_0_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["1 Sinuous Single Thread"]}}]}'
WHERE machine_name = 'stage_1_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["2 Channelized"]}}]}'
WHERE machine_name = 'stage_2_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["3 Degradation"]}}]}'
WHERE machine_name = 'stage_3_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["4 Degradation and Widening"]}}]}'
WHERE machine_name = 'stage_4_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["5 Aggradation and Widening"]}}]}'
WHERE machine_name = 'stage_5_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["6 Quasi Equilibrium"]}}]}'
WHERE machine_name = 'stage_6_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["7 Laterally Active"]}}]}'
WHERE machine_name = 'stage_7_area';

UPDATE metrics SET
    metadata = '{"minimum_value": 0.0, "precision": 3}',
    metric_params = '{"dce_layers": [{"layer_id_ref": "cem_phases", "attribute_filter": {"field_id_ref": "sem_stage", "values": ["8 Anastomosing"]}}]}'
WHERE machine_name = 'stage_8_area';

PRAGMA foreign_keys=ON;