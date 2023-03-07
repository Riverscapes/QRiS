"""Methods for generating analysis metrics."""

import math
import json

import osgeo
from osgeo import ogr, gdal, osr


def get_utm_zone_epsg(longitude: float) -> int:
    """Really crude EPSG lookup method

    Args:
        longitude (float): [description]

    Returns:
        int: [description]
    """
    zone_number = math.floor((180.0 + longitude) / 6.0)
    epsg = 26901 + zone_number
    return epsg


def count(project_file: str, mask_feature_id: int, inputs: str) -> int:
    """Count the number of features in the specified layers that intersect the mask feature.

       CalculationID: 1
    """

    metric_layers = json.loads(inputs)
    ds = ogr.Open(project_file)
    mask_layer = ds.GetLayerByName('mask_features')
    src_srs = mask_layer.GetSpatialRef()  # TODO  check if we need any transformations
    mask_layer.SetAttributeFilter(f"mask_id = {mask_feature_id}")
    mask_feature = mask_layer.GetNextFeature()
    mask_geom = mask_feature.GetGeometryRef().Clone()

    feature_count = 0
    for layer_name in metric_layers['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        # src_srs = mask_layer.GetSpatialRef()
        layer.SetSpatialFilter(mask_geom)
        feature_count += layer.GetFeatureCount()

    return feature_count


def length(project_file: str, mask_feature_id: int, inputs: str):
    """Get the total length of the features in the specified layers that intersect the mask feature.

       CalculationID: 2
    """

    metric_layers = json.loads(inputs)
    ds = ogr.Open(project_file)
    mask_layer = ds.GetLayerByName('mask_features')
    src_srs = mask_layer.GetSpatialRef()  # TODO  check if we need any transformations
    mask_layer.SetAttributeFilter(f"mask_id = {mask_feature_id}")
    mask_feature = mask_layer.GetNextFeature()
    mask_geom = mask_feature.GetGeometryRef().Clone()

    total_length = 0
    for layer_name in metric_layers['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        layer.SetSpatialFilter(mask_geom)
        for feature in layer:
            geom = feature.GetGeometryRef().Clone()
            if geom.Intersects(mask_geom):
                clipped_geom = geom.Intersection(mask_geom)
                epsg = get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                total_length += clipped_geom.Length()

    return total_length


def area(project_file: str, mask_feature_id: int, inputs: str):
    """Get the total area of the features in the specified layers that intersect the mask feature.

       CalculationID: 3
    """

    metric_layers = json.loads(inputs)
    ds = ogr.Open(project_file)
    mask_layer = ds.GetLayerByName('mask_features')
    src_srs = mask_layer.GetSpatialRef()  # TODO  check if we need any transformations
    mask_layer.SetAttributeFilter(f"mask_id = {mask_feature_id}")
    mask_feature = mask_layer.GetNextFeature()
    mask_geom = mask_feature.GetGeometryRef().Clone()

    total_area = 0
    for layer_name in metric_layers['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        layer.SetSpatialFilter(mask_geom)
        for feature in layer:
            geom = feature.GetGeometryRef()
            if geom.Intersects(mask_geom):
                clipped_geom = geom.Intersection(mask_geom)
                epsg = get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                total_area += clipped_geom.Area()

    return total_area
