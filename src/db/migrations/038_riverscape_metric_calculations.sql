INSERT INTO calculations (name, metric_function)
SELECT 'Elevation', 'elevation'
WHERE NOT EXISTS (
    SELECT 1 FROM calculations WHERE metric_function = 'elevation'
);
