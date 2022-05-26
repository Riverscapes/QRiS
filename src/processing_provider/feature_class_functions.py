from osgeo import ogr
from osgeo import osr
from shapely.wkb import loads as wkbload, dumps as wkbdumps


def check_geometry_type(path) -> int:

    ds = ogr.Open(path)
    layer = ds.GetLayer(0)
    return layer.GetGeomType()


def import_mask(source_path: str, dest_path: str, mask_id: int) -> None:

    src_path, src_layer_name = source_path.split('|layername=')
    src_dataset = ogr.Open(src_path)
    src_layer = src_dataset.GetLayer(src_layer_name if src_layer_name is not None else 0)
    src_srs = src_layer.GetSpatialRef()
    # mask_id_field_index = src_layer

    gpkg_driver = ogr.GetDriverByName('GPKG')
    dst_dataset = gpkg_driver.Open(dest_path, 1)
    dst_layer = dst_dataset.GetLayerByName('mask_features')
    dst_srs = dst_layer.GetSpatialRef()
    dst_layer_def = dst_layer.GetLayerDefn()

    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    for src_feature in src_layer:
        geom = src_feature.GetGeometryRef()
        print(geom.IsValid())
        geom.Transform(transform)
        # print(geom.ExportToJson())
        print(geom.IsValid())

        dst_feature = ogr.Feature(dst_layer_def)
        dst_feature.SetGeometry(geom)
        dst_feature.SetField('mask_id', mask_id)
        dst_feature.SetField('fid', 1)
        err = dst_layer.CreateFeature(dst_feature)
        print(err)
        dst_feature = None

    # dst_feature = None
    src_dataset = None
    dst_dataset = None
