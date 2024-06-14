ALTER TABLE metrics ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Add Unique key to metrics table based on machine code and version
--ALTER TABLE metrics ADD CONSTRAINT pk_metrics PRIMARY KEY (machine_code, version);
-- not supported in sqlite, so make sure to not insert duplicate machine_code and version in python code

-- Update version for dam_density and jam_density
UPDATE metrics SET version = 1 WHERE machine_name = 'dam_density';
UPDATE metrics SET version = 1 WHERE machine_name = 'jam_density';
