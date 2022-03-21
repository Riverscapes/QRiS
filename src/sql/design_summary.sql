-- Structures Detailed
CREATE VIEW structures_detailed AS
SELECT designs.FID AS [Design ID], designs.name AS [Design Name], lkp_design_status.name AS [Design Status], phases.name AS [Phase Name], structure_types.name AS [Structure Type], lkp_structure_mimics.name AS [Structure Mimics], Count(structure_points.FID) AS [Structure Count]
FROM phases
    INNER JOIN ((lkp_structure_mimics INNER JOIN structure_types ON lkp_structure_mimics.FID = structure_types.mimics_id)
        INNER JOIN (lkp_design_status INNER JOIN (designs INNER JOIN structure_points ON designs.FID = structure_points.design_id) ON lkp_design_status.FID = designs.status_id) ON structure_types.FID = structure_points.structure_type_id) ON phases.FID = structure_points.phase_id
GROUP BY designs.FID, designs.name, lkp_design_status.name, phases.name, structure_types.name, lkp_structure_mimics.name;

INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ("structures_detailed", "attributes", "structures_detailed", 0);

