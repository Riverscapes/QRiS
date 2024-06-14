INSERT INTO lkp_event_types (id, name) VALUES (4, 'Planning');

INSERT INTO protocols (id, name, machine_code, has_custom_ui) VALUES (6, 'Planning', 'PLANNING', 0);
INSERT INTO methods (id, name, machine_code) VALUES (7, 'Planning', 'PLANNING');
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (6, 7);

INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (40, 'recovery_potential', 'Recovery Potential', 'recovery_potential.qml', 0, 'Polygon', '{"hierarchy": ["Assessments"]}');
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (41, 'risk_potential_points', 'Risk Potential', 'risk_potential_points.qml', 0, 'Point', '{"hierarchy": ["Assessments"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}]}}');
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (42, 'risk_potential_lines', 'Risk Potential', 'risk_potential_lines.qml', 0, 'Linestring', '{"hierarchy": ["Assessments"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}]}');
INSERT INTO layers (id, fc_name, display_name, qml, is_lookup, geom_type, metadata) VALUES (43, 'risk_potential_polygons', 'Risk Potential', 'risk_potential_polygons.qml', 0, 'Polygon', '{"hierarchy": ["Assessments"], "fields": [{"machine_code": "risk_type", "label": "Risk", "type": "list", "lookup": "risk_type"}]}');

INSERT INTO method_layers (method_id, layer_id) VALUES (7, 40);
INSERT INTO method_layers (method_id, layer_id) VALUES (7, 41);
INSERT INTO method_layers (method_id, layer_id) VALUES (7, 42);
INSERT INTO method_layers (method_id, layer_id) VALUES (7, 43);

INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type', 'Low');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type', 'Medium');
INSERT INTO lookup_list_values (list_name, list_value) VALUES ('risk_type', 'High');