INSERT INTO calculations (name, metric_function)
SELECT 'manual', 'manual'
WHERE NOT EXISTS (
    SELECT 1 FROM calculations WHERE metric_function = 'manual'
);
