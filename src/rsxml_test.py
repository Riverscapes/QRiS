import rsxml
from rsxml import Logger
from datetime import date
from rsxml.project_xml import Project, ProjectBounds, Coords, BoundingBox, MetaData, Meta, Realization, Dataset, GeoPackageDatasetTypes


def rsxml_test():
    log = Logger('Project')
    size_test = rsxml.get_obj_size('SIZEOFME')
    log.debug(f'Size of SIZEOFME: {size_test}')

    # Create a project
    project = Project(
        name='Test Project',
        proj_path='DELETEME.rs.xml',
        project_type='VBET',
        description='This is a test project',
        citation='This is a citation',
        bounds=ProjectBounds(
            centroid=Coords(-21.23, 114.56),
            bounding_box=BoundingBox(-22, -21, 114, 116),
            filepath='project_bounds.json',
        ),
        meta_data=MetaData(values=[Meta('Test', 'Test Value')]),
        realizations=[
            Realization(
                xml_id='test',
                name='Test Realization',
                product_version='1.0.0',
                date_created=date(2021, 1, 1),
                summary='This is a test realization',
                description='This is a test realization',
                meta_data=MetaData(values=[Meta('Test', 'Test Value')]),
                inputs=[
                    Dataset(
                        xml_id='input1',
                        name='InputDS1',
                        path='datasets/input1.tiff',
                        ds_type=GeoPackageDatasetTypes.RASTER,
                        summary='This is a input dataset',
                        description='This is a input dataset',
                    )
                ],
                intermediates=[
                    Dataset(
                        xml_id='inter1',
                        name='inter1DS',
                        path='datasets/inter1.tiff',
                        ds_type=GeoPackageDatasetTypes.RASTER,
                        summary='This is a input dataset',
                        description='This is a input dataset',
                    )
                ],
                outputs=[
                    Dataset(
                        xml_id='output1',
                        name='OutputDS1',
                        path='datasets/output.tiff',
                        ds_type=GeoPackageDatasetTypes.RASTER,
                        summary='This is a input dataset',
                        description='This is a input dataset',
                    )
                ]
            )
        ]
    )
    project.write()
    log.info('Project created')
