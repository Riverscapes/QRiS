ALTER TABLE rasters ADD COLUMN is_context BOOLEAN DEFAULT 0;

INSERT INTO lkp_raster_types (id, name) VALUES (6, 'Hillshade');

INSERT INTO method_layers (method_id, layer_id) VALUES (3, 5);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 7);