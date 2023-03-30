"""Methods for generating analysis metrics."""

import os
import math

import osgeo
from osgeo import ogr, gdal, osr

from .zonal_statistics import zonal_statistics


class MetricInputMissingError(Exception):
    """Raised when a metric input is missing."""
    pass


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


def get_mask_geom(project_file: str, mask_feature_id: int) -> ogr.Geometry:
    """Get the geometry of the mask feature.

    Args:
        project_file (str): [description]
        mask_feature_id (int): [description]

    Returns:
        ogr.Geometry: [description]
    """
    ds = ogr.Open(project_file)
    mask_layer = ds.GetLayerByName('mask_features')
    mask_layer.SetAttributeFilter(f"fid = {mask_feature_id}")
    mask_feature = mask_layer.GetNextFeature()
    mask_geom = mask_feature.GetGeometryRef().Clone()
    return mask_geom


def count(project_file: str, mask_feature_id: int, event_id: int, metric_params: dict) -> int:
    """Count the number of features in the specified layers that intersect the mask feature.

       CalculationID: 1
    """

    mask_geom = get_mask_geom(project_file, mask_feature_id)

    feature_count = 0
    for layer_name in metric_params['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        layer.SetAttributeFilter(f"event_id = {event_id}")
        layer.SetSpatialFilter(mask_geom)
        feature_count += layer.GetFeatureCount()

    return feature_count


def length(project_file: str, mask_feature_id: int, event_id: int, metric_params: dict):
    """Get the total length of the features in the specified layers that intersect the mask feature.

       CalculationID: 2
    """

    mask_geom = get_mask_geom(project_file, mask_feature_id)

    total_length = 0
    for layer_name in metric_params['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        layer.SetAttributeFilter(f"event_id = {event_id}")
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


def area(project_file: str, mask_feature_id: int, event_id: int, metric_params: dict):
    """Get the total area of the features in the specified layers that intersect the mask feature.

       CalculationID: 3
    """

    mask_geom = get_mask_geom(project_file, mask_feature_id)

    total_area = 0
    for layer_name in metric_params['layers']:
        ds = ogr.Open(project_file)
        layer = ds.GetLayerByName(layer_name)
        layer.SetAttributeFilter(f"event_id = {event_id}")
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


def sinuosity(project_file: str, mask_feature_id: int, event_id: int, metric_params: str):
    """Get the sinuosity of the features in the specified layers that intersect the mask feature.

       CalculationID: 4
    """

    # TODO Note that centerlines are not currently associated with an event_id, so the event_id is not used in this calculation.

    mask_geom = get_mask_geom(project_file, mask_feature_id)

    layer_name = metric_params['layers'][0]
    ds = ogr.Open(project_file)
    layer = ds.GetLayerByName(layer_name)
    # layer.SetAttributeFilter(f"event_id = {event_id}")
    layer.SetSpatialFilter(mask_geom)
    feature = layer.GetNextFeature()
    if feature is None:
        raise MetricInputMissingError(f'No features found in {layer_name} that intersect the mask feature.')
    geom = feature.GetGeometryRef().Clone()

    clipped_geom = geom.Intersection(mask_geom)
    epsg = get_utm_zone_epsg(geom.Centroid().GetX())
    utm_srs = osr.SpatialReference()
    utm_srs.ImportFromEPSG(epsg)
    clipped_geom.TransformTo(utm_srs)
    length = clipped_geom.Length()
    segment_geom = ogr.Geometry(ogr.wkbLineString)
    start_pt = clipped_geom.GetPoint(0)
    end_pt = clipped_geom.GetPoint(clipped_geom.GetPointCount() - 1)
    segment_geom.AddPoint(start_pt[0], start_pt[1])
    segment_geom.AddPoint(end_pt[0], end_pt[1])
    distance = segment_geom.Length()

    return length / distance


def gradient(project_file: str, mask_feature_id: int, event_id: int, metric_params: dict):
    """Get the gradient of the features in the specified layers that intersect the mask feature.

       CalculationID: 5
    """

    raster_layer = metric_params['rasters']['Digital Elevation Model (DEM)']['path']
    if not os.path.exists(raster_layer):
        raise Exception(f'Expected Raster layer {raster_layer} does not exist.')

    mask_geom = get_mask_geom(project_file, mask_feature_id)

    layer_name = metric_params['layers'][0]
    ds = ogr.Open(project_file)
    layer = ds.GetLayerByName(layer_name)
    layer.SetSpatialFilter(mask_geom)
    feature = layer.GetNextFeature()
    if feature is None:
        raise MetricInputMissingError(f'No features found in {layer_name} that intersect the mask feature.')
    geom = feature.GetGeometryRef().Clone()

    epsg = get_utm_zone_epsg(geom.Centroid().GetX())
    utm_srs = osr.SpatialReference()
    utm_srs.ImportFromEPSG(epsg)

    clipped_geom = geom.Intersection(mask_geom)
    clipped_geom.TransformTo(utm_srs)
    start_pt = clipped_geom.GetPoint(0)
    end_pt = clipped_geom.GetPoint(clipped_geom.GetPointCount() - 1)
    point_start = ogr.Geometry(ogr.wkbPoint)
    point_start.AssignSpatialReference(utm_srs)
    point_start.AddPoint(start_pt[0], start_pt[1])
    point_end = ogr.Geometry(ogr.wkbPoint)
    point_end.AssignSpatialReference(utm_srs)
    point_end.AddPoint(end_pt[0], end_pt[1])

    buffer_start = point_start.Buffer(10)
    buffer_end = point_end.Buffer(10)

    stats_start = zonal_statistics(raster_layer, buffer_start)
    stats_end = zonal_statistics(raster_layer, buffer_end)

    length = clipped_geom.Length()

    return (stats_end['minimum'] - stats_start['minimum']) / length
