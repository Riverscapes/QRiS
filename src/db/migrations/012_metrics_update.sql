ALTER TABLE metrics ADD COLUMN machine_name TEXT NOT NULL DEFAULT '';

UPDATE metrics SET machine_name = 'dam_density' WHERE name = 'Dam Density';
UPDATE metrics SET machine_name = 'jam_density' WHERE name = 'Jam Density';