INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_cer', 'high');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_cer', 'medium');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_cer', 'low');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_type', 'active_dam');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_type', 'inactive_dam');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('dam_type', 'relic');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('type_cer', 'high');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('type_cer', 'medium');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('type_cer', 'low');

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'bank_lodge');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'bank_den');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'pond_lodge');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'chew_stick');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'clipped_vegetation');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'felled_tree');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'harvested_branches');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'food_cache');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'slide');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'canal');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'scat');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'set_of_tracks');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'scent_mound');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'skid_trail');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'pond_excavation');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('beaver_sign_type', 'other');

INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (44, 'beaver_dam', 'Beaver Dam', 'beaver_dam.qml', 0, 'Point', '{"hierarchy": ["Observations", "Beaver Activity"], "fields": [{"machine_code": "dam_cer", "label": "Dam CER", "type": "list", "lookup": "dam_cer"}, {"machine_code": "dam_type", "label": "Dam Type", "type": "list", "lookup": "dam_type"}, {"machine_code": "type_cer", "label": "Type CER", "type": "list", "lookup": "type_cer"}]}');
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (45, 'beaver_sign', 'Beaver Sign', 'beaver_sign.qml', 0, 'Point', '{"hierarchy": ["Observations", "Beaver Activity"], "fields": [{"machine_code": "sign_type", "label": "Type", "type": "list", "lookup": "beaver_sign_type"}]}');

INSERT INTO method_layers (method_id, layer_id) VALUES (1, 44);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 45);