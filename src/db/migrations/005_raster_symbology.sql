-- Description: add symbology column and values to raster types
-- Date: 2023-04-14
ALTER TABLE lkp_context_layer_types ADD COLUMN symbology TEXT;
UPDATE lkp_context_layer_types SET symbology = 'Shared/dem.qml' WHERE id = 2;
UPDATE lkp_context_layer_types SET symbology = 'Shared/Hillshade.qml' WHERE id = 5;
UPDATE lkp_context_layer_types SET symbology = 'Shared/slope.qml' WHERE id = 6;
UPDATE lkp_context_layer_types SET symbology = 'VBET/vbetLikelihood.qml' WHERE id = 7;

ALTER TABLE lkp_raster_types ADD COLUMN symbology TEXT;
UPDATE lkp_raster_types SET symbology = 'Shared/dem.qml' WHERE id = 4;
UPDATE lkp_raster_types SET symbology = 'VBET/vbetLikelihood.qml' WHERE id = 5;
UPDATE lkp_raster_types SET symbology = 'Shared/Hillshade.qml' WHERE id = 6;
