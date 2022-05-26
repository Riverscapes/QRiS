from osgeo import ogr
from osgeo import osr
from shapely.wkb import loads as wkbload, dumps as wkbdumps
from osgeo.gdal import Warp, WarpOptions


def check_geometry_type(path) -> int:

    ds = ogr.Open(path)
    layer = ds.GetLayer(0)
    return layer.GetGeomType()


def import_mask(source_path: str, dest_path: str, mask_id: int) -> None:

    ogr.UseExceptions()

    src_path, src_layer_name = source_path.split('|layername=')
    src_dataset = ogr.Open(src_path)
    src_layer = src_dataset.GetLayer(src_layer_name if src_layer_name is not None else 0)
    src_srs = src_layer.GetSpatialRef()

    gpkg_driver = ogr.GetDriverByName('GPKG')
    dst_dataset = gpkg_driver.Open(dest_path, 1)
    dst_layer = dst_dataset.GetLayerByName('mask_features')
    dst_srs = dst_layer.GetSpatialRef()
    dst_layer_def = dst_layer.GetLayerDefn()

    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    for src_feature in src_layer:
        geom = src_feature.GetGeometryRef()
        geom.Transform(transform)
        # print(geom.ExportToJson())

        dst_feature = ogr.Feature(dst_layer_def)
        dst_feature.SetGeometry(geom)
        dst_feature.SetField('mask_id', mask_id)
        err = dst_layer.CreateFeature(dst_feature)
        dst_feature = None

    src_dataset = None
    dst_dataset = None


def copy_raster_to_project(source_path: str, mask_tuple, output_path: str) -> None:
    """
    https://gdal.org/python/osgeo.gdal-module.html#WarpOptions
    https://gis.stackexchange.com/questions/278627/using-gdal-warp-and-gdal-warpoptions-of-gdal-python-api
    """

    # You can use this WarpOptions to get a list of the possible options
    # wo = WarpOptions(format: 'GTiff', cutl)

    kwargs = {'format': 'GTiff'}
    if mask_tuple is not None:
        kwargs['cutlineDSName'] = mask_tuple[0]
        kwargs['cutlineLayer'] = 'mask_features'
        kwargs['cutlineWhere'] = 'mask_id = {}'.format(mask_tuple[1])

    Warp(output_path, source_path, **kwargs)
