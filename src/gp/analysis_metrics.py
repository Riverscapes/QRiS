"""Methods for generating analysis metrics."""

import os
import math
import json
import sqlite3
from typing import Generator

import osgeo
from osgeo import ogr, gdal, osr

from qgis.core import QgsUnitTypes

from .zonal_statistics import zonal_statistics

from ..model.db_item import DBItem
from ..model.layer import Layer
from ..model.profile import Profile
from ..model.raster import Raster

analysis_metric_unit_type = {
    'count': 'count',
    'length': 'distance',
    'area': 'area',
    'sinuosity': 'ratio',
    'gradient': 'ratio',
    'area_proportion': 'ratio'
}

class MetricInputMissingError(Exception):
    """Raised when a metric input is missing."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class MetricCalculationError(Exception):
    """Raised when a metric calculation fails."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def normalization_factor(project_file: str, sample_frame_feature_id: int, profile: Profile) -> float:

    # clip the profile to the mask feature
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    ds: ogr.DataSource = ogr.Open(project_file)
    profile_layer: ogr.Layer = ds.GetLayerByName(profile.fc_name)
    profile_layer.SetAttributeFilter(f"profile_id = {profile.id}")
    profile_feature: ogr.Feature = profile_layer.GetNextFeature()
    profile_geom: ogr.Geometry = profile_feature.GetGeometryRef().Clone()

    clipped_geom = profile_geom.Intersection(sample_frame_geom)
    epsg = get_utm_zone_epsg(profile_geom.Centroid().GetX())
    utm_srs = osr.SpatialReference()
    utm_srs.ImportFromEPSG(epsg)
    clipped_geom.TransformTo(utm_srs)
    length = clipped_geom.Length()
    
    return length


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


def get_sample_frame_geom(project_file: str, sample_frame_feature_id: int) -> ogr.Geometry:
    """Get the geometry of the sample frame feature.

    Args:
        project_file (str): source qris gpkg path
        sample_frame_feature_id (int): sample frame feature id

    Returns:
        ogr.Geometry: sample frame polygon geometry
    """
    ds: ogr.DataSource = ogr.Open(project_file)
    sample_frame_layer: ogr.Layer = ds.GetLayerByName('sample_frame_features')
    sample_frame_layer.SetAttributeFilter(f"fid = {sample_frame_feature_id}")
    sample_frame_feature: ogr.Feature = sample_frame_layer.GetNextFeature()
    sample_frame_geom: ogr.Geometry = sample_frame_feature.GetGeometryRef().Clone()
    return sample_frame_geom

def get_clipped_input_geom(project_file, sample_frame_feature_id, db_item: DBItem) -> ogr.Geometry:
    """Get the geometry of the input feature clipped to the sample frame feature.

    Args:
        project_file (str): source qris gpkg path
        sample_frame_feature_id (int): sample frame feature id
        input_name (str): input feature name
        input_id (int): input feature id

    Returns:
        ogr.Geometry: input feature geometry
    """
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    ds: ogr.DataSource = ogr.Open(project_file)
    layer: ogr.Layer = ds.GetLayerByName(db_item.fc_name)
    layer.SetAttributeFilter(f"{db_item.id_column_name} = {db_item.id}")
    feature: ogr.Feature = layer.GetNextFeature()
    geom: ogr.Geometry = feature.GetGeometryRef().Clone()

    clipped_geom = geom.Intersection(sample_frame_geom)
    epsg = get_utm_zone_epsg(geom.Centroid().GetX())
    utm_srs = osr.SpatialReference()
    utm_srs.ImportFromEPSG(epsg)
    clipped_geom.TransformTo(utm_srs)

    return clipped_geom

def get_dce_layer_source(project_file: str, machine_code: str) -> tuple[str, int]:

    with sqlite3.connect(project_file, timeout=10.0) as conn:
        c = conn.cursor()
        c.execute(f"SELECT id, geom_type FROM layers WHERE fc_name = '{machine_code}'")
        layer_data = c.fetchone()
        if layer_data is None:
            return None, None
            # raise MetricInputMissingError(f'Required Layer {machine_code} not found in project.')
        layer_id = layer_data[0]
        geom_type = layer_data[1]
        layer_source = Layer.DCE_LAYER_NAMES[geom_type]
    
    return layer_id, layer_source


def get_metric_layer_features(
    project_file: str,
    metric_layer: dict,
    event_id: int,
    sample_frame_geom: ogr.Geometry,
    analysis_params: dict
) -> Generator[ogr.Feature, None, None]:
    """Get the features of the metric layer that intersect the sample frame geometry.

    Args:
        project_file (str): Source QRIS GPKG path.
        metric_layer (dict): Metric layer configuration.
        event_id (int): Event ID.
        sample_frame_geom (ogr.Geometry): Sample frame geometry.
        analysis_params (dict): Analysis parameters.

    Yields:
        ogr.Feature: Features of the metric layer.
    """
    ds = None
    layer = None
    try:
        if metric_layer.get('input_ref', None) is not None:
            if metric_layer['usage'] == 'surface':
                return None
            analysis_param = analysis_params.get(metric_layer['input_ref'], None)
            if analysis_param is None:
                raise MetricInputMissingError(f'Missing input reference {metric_layer["input_ref"]} in analysis parameters. Has this been specified in the analysis paramenters?')
            db_item = analysis_params[metric_layer['input_ref']]
            ds: ogr.DataSource = ogr.Open(project_file)
            layer: ogr.Layer = ds.GetLayerByName(db_item.fc_name)
            layer.SetAttributeFilter(f"{db_item.fc_id_column_name} = {db_item.id}")
        else:
            layer_id, layer_name = get_dce_layer_source(project_file, metric_layer['layer_id_ref'])
            if layer_id is None:
                return None
            ds: ogr.DataSource = ogr.Open(project_file)
            layer: ogr.Layer = ds.GetLayerByName(layer_name)
            layer.SetAttributeFilter(f"event_id = {event_id} and event_layer_id = {layer_id}")
            layer.SetSpatialFilter(sample_frame_geom)
        
        attribute_filter = metric_layer.get('attribute_filter', None)
        for feature in layer:
            if attribute_filter is not None:
                metadata_value = feature.GetField('metadata')
                if metadata_value is None:
                    continue
                metadata: dict = json.loads(metadata_value)
                attributes: dict = metadata.get('attributes', None)
                
                if attributes is None:
                    attributes = {}
                
                field_ref = attribute_filter['field_id_ref']
                
                if field_ref not in attributes:
                    raise MetricCalculationError(f"Feature {feature.GetFID()} is missing required attribute '{field_ref}' for filtering.")

                val = attributes[field_ref]
                if val is None or val == 'NULL' or val == '':
                    raise MetricCalculationError(f"Feature {feature.GetFID()} has a NULL value for required attribute '{field_ref}'.")

                if val not in attribute_filter['values']:
                    continue

            yield feature
            feature = None
            
    finally:
        layer = None
        ds = None


def count(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict) -> int:
    """Count the number of features in the specified layers that intersect the mask feature.
    
        CalculationID: 1
    """
    
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    total_feature_count = 0
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    for metric_layer in metric_layers:
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            feature_count = 0

            # Handle the optional count_field
            count_fields = metric_layer.get('count_fields', None)
            if count_fields is not None:
                for count_field in count_fields:
                    count_field_name = count_field.get('field_id_ref', None)
                    metadata_value = feature.GetField('metadata')
                    metadata = json.loads(metadata_value) if metadata_value is not None else {}
                    attributes: dict = metadata.get('attributes', {})
                    attribute_value = attributes.get(count_field_name, 0)
                    attribute_value = 1 if attribute_value is None else attribute_value
                    feature_count += int(attribute_value)
                if feature_count == 0:
                    # If no count fields are specified, default to 1
                    feature_count = 1
            else:
                feature_count += 1
            
            geom: ogr.Geometry = feature.GetGeometryRef()
            if geom is None:
                continue
            if ogr.GT_Flatten(geom.GetGeometryType()) in [ogr.wkbLineString, ogr.wkbPolygon, ogr.wkbMultiPolygon, ogr.wkbMultiLineString]:
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                epsg = get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                geom.TransformTo(utm_srs)
                if ogr.GT_Flatten(geom.GetGeometryType()) in [ogr.wkbLineString, ogr.wkbMultiLineString]:
                    proportion = clipped_geom.Length() / geom.Length()
                else:
                    proportion = clipped_geom.Area() / geom.Area()
                feature_count *= proportion
                clipped_geom = None
            total_feature_count += round(feature_count)

    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            layer_ref = metric_layer.get('input_ref', None)
            if layer_ref is not None:
                normalization = normalization_factor(project_file, sample_frame_feature_id, analysis_params[layer_ref])
                total_feature_count /= normalization

    return total_feature_count


def length(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    """Get the total length of the features in the specified layers that intersect the mask feature.

       CalculationID: 2
    """

    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)
    total_length = 0
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            continue
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                epsg = get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                total_length += clipped_geom.Length()
            geom = None
            clipped_geom = None

    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            layer_ref = metric_layer.get('input_ref', None)
            if layer_ref is not None:
                normalization = normalization_factor(project_file, sample_frame_feature_id, analysis_params[layer_ref])
                total_length /= normalization

    return total_length


def area(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    """Get the total area of the features in the specified layers that intersect the mask feature.

       CalculationID: 3
    """

    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    total_area = 0
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            continue
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if not geom.IsValid():
                geom = geom.MakeValid()
            if geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                epsg = get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                total_area += clipped_geom.GetArea()
            geom = None
            clipped_geom = None

    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            layer_ref = metric_layer.get('input_ref', None)
            if layer_ref is not None:
                normalization = normalization_factor(project_file, sample_frame_feature_id, analysis_params[layer_ref])
                total_area /= normalization

    return total_area


def sinuosity(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    """
    Calculate the sinuosity of all line features in the specified layer(s) that intersect the sample frame,
    by unioning all segments before calculation.
    """
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    metric_layer = metric_layers[0]  # Sinuosity only uses one layer

    # Collect all clipped line geometries
    line_geoms = []
    
    for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
        if feature is None:
             continue
        geom: ogr.Geometry = feature.GetGeometryRef().Clone()
        if not geom.IsValid():
            geom = geom.MakeValid()
        
        if geom.Intersects(sample_frame_geom):
            clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
            if clipped_geom is None or clipped_geom.IsEmpty():
                continue
            
            # Only consider line geometries
            if ogr.GT_Flatten(clipped_geom.GetGeometryType()) in [ogr.wkbLineString, ogr.wkbMultiLineString]:
                epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                line_geoms.append(clipped_geom)

    # Union all line geometries
    if not line_geoms:
        return 0.0
    union_geom = line_geoms[0].Clone()
    for g in line_geoms[1:]:
        union_geom = union_geom.Union(g)

    # If union results in MultiLineString, convert to LineString if possible
    if ogr.GT_Flatten(union_geom.GetGeometryType()) == ogr.wkbMultiLineString and union_geom.GetGeometryCount() == 1:
        union_geom = union_geom.GetGeometryRef(0).Clone()

    # Calculate sinuosity
    g_type_flat = ogr.GT_Flatten(union_geom.GetGeometryType())
    if g_type_flat not in [ogr.wkbLineString, ogr.wkbMultiLineString]:
        return 0.0
    
    # Handle MultiLineString specifically for points extraction
    if g_type_flat == ogr.wkbMultiLineString:
        # Check if we can just take start of first and end of last?
        pass

    if union_geom.GetPointCount() < 2:
        return 0.0

    length = union_geom.Length()
    start_pt = union_geom.GetPoint(0)
    end_pt = union_geom.GetPoint(union_geom.GetPointCount() - 1)
    segment_geom = ogr.Geometry(ogr.wkbLineString)
    segment_geom.AddPoint(start_pt[0], start_pt[1])
    segment_geom.AddPoint(end_pt[0], end_pt[1])
    distance = segment_geom.Length()
    if distance == 0:
        return 0.0

    return length / distance


def gradient(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    """Get the gradient of the features in the specified layers that intersect the mask feature.

       CalculationID: 5
    """

    surface: Raster = None
    for input_param in metric_params.get('inputs', []):
        if input_param.get('usage', None) == 'surface':
            surface = analysis_params.get(input_param.get('input_ref', None), None)
            break
    raster_layer = os.path.join(os.path.dirname(project_file), surface.path)
    if not os.path.exists(raster_layer):
        raise Exception(f'Expected Raster layer {raster_layer} does not exist.')

    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    line_geoms = []
    for metric_layer in metric_layers:
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if not geom.IsValid():
                geom = geom.MakeValid()
            if geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                if clipped_geom is None or clipped_geom.IsEmpty():
                    continue
                if ogr.GT_Flatten(clipped_geom.GetGeometryType()) in [ogr.wkbLineString, ogr.wkbMultiLineString]:
                    epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                    utm_srs = osr.SpatialReference()
                    utm_srs.ImportFromEPSG(epsg)
                    clipped_geom.TransformTo(utm_srs)
                    line_geoms.append(clipped_geom)
    if not line_geoms:
        raise MetricInputMissingError('No line features found for gradient calculation.')

    # Union all line geometries
    union_geom = line_geoms[0].Clone()
    for g in line_geoms[1:]:
        union_geom = union_geom.Union(g)
    if ogr.GT_Flatten(union_geom.GetGeometryType()) == ogr.wkbMultiLineString and union_geom.GetGeometryCount() == 1:
        union_geom = union_geom.GetGeometryRef(0).Clone()

    if ogr.GT_Flatten(union_geom.GetGeometryType()) not in [ogr.wkbLineString, ogr.wkbMultiLineString]:
        raise MetricCalculationError('Unioned geometry is not a line.')
    if union_geom.GetPointCount() < 2:
        raise MetricCalculationError('Unioned geometry does not have enough points.')

    start_pt = union_geom.GetPoint(0)
    end_pt = union_geom.GetPoint(union_geom.GetPointCount() - 1)
    utm_srs = union_geom.GetSpatialReference()
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

    length = union_geom.Length()
    if length == 0:
        raise MetricCalculationError('Unioned geometry has zero length.')

    return (stats_end['minimum'] - stats_start['minimum']) / length


def area_proportion(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])

    numerator_layers = [layer for layer in metric_layers if layer.get('usage', 'numerator').lower() in ['numerator', 'input']]
    numerator_area = 0.0
        
    for metric_layer in numerator_layers:
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if not geom.IsValid():
                geom = geom.MakeValid()
            if geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                if clipped_geom is None or clipped_geom.IsEmpty():
                    geom = None
                    clipped_geom = None
                    continue
                epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                numerator_area += clipped_geom.GetArea()
            geom = None
            clipped_geom = None

    denominator_layers = [layer for layer in metric_layers if str(layer.get('usage', '')).lower() == 'denominator']
    denominator_area = 0.0

    if len(denominator_layers) == 0:
        # use the sample frame area as the denominator
        epsg = get_utm_zone_epsg(sample_frame_geom.Centroid().GetX())
        utm_srs = osr.SpatialReference()
        utm_srs.ImportFromEPSG(epsg)
        proj_sample_frame_geom = sample_frame_geom.Clone()
        proj_sample_frame_geom.TransformTo(utm_srs)
        denominator_area = proj_sample_frame_geom.GetArea()
    else:
        for metric_layer in denominator_layers:
            for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
                if feature is None:
                    continue
                geom: ogr.Geometry = feature.GetGeometryRef().Clone()
                if not geom.IsValid():
                    geom = geom.MakeValid() # Added MakeValid for consistency
                if geom.Intersects(sample_frame_geom):
                    clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                    if clipped_geom is None or clipped_geom.IsEmpty():
                         geom = None
                         clipped_geom = None
                         continue
                    epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                    utm_srs = osr.SpatialReference()
                    utm_srs.ImportFromEPSG(epsg)
                    clipped_geom.TransformTo(utm_srs)
                    denominator_area += clipped_geom.GetArea()
                geom = None
                clipped_geom = None

    if denominator_area == 0.0:
        return 0.0
    else:
        return numerator_area / denominator_area
    

def proportion(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    
    # Initialize the sample frame geometry
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    
    # Numerator Layers
    numerator_layers = [layer for layer in metric_layers if layer.get('usage', 'numerator').lower() == 'numerator']
    numerator_value = 0.0    
    for metric_layer in numerator_layers:
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if not geom.IsValid():
                geom = geom.MakeValid()
            if geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                if clipped_geom is None or clipped_geom.IsEmpty():
                    geom = None
                    clipped_geom = None
                    continue
                epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                clipped_geom.TransformTo(utm_srs)
                numerator_value += clipped_geom.GetArea() if ogr.GT_Flatten(clipped_geom.GetGeometryType()) in [ogr.wkbPolygon, ogr.wkbMultiPolygon] else clipped_geom.Length()
            geom = None
            clipped_geom = None

    # Denominator Layers
    denominator_layers = [layer for layer in metric_layers if str(layer.get('usage', '')).lower() == 'denominator']
    denominator_value = 0.0
    if len(denominator_layers) == 0:
        # use the sample frame area as the denominator
        epsg = get_utm_zone_epsg(sample_frame_geom.Centroid().GetX())
        utm_srs = osr.SpatialReference()
        utm_srs.ImportFromEPSG(epsg)
        proj_sample_frame_geom = sample_frame_geom.Clone()
        proj_sample_frame_geom.TransformTo(utm_srs)
        denominator_value = proj_sample_frame_geom.GetArea()
    else:
        for metric_layer in denominator_layers:
            for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
                if feature is None:
                    continue
                geom: ogr.Geometry = feature.GetGeometryRef().Clone()
                if geom.Intersects(sample_frame_geom):
                    clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                    if clipped_geom is None or clipped_geom.IsEmpty():
                        geom = None
                        clipped_geom = None
                        continue
                    epsg = get_utm_zone_epsg(clipped_geom.Centroid().GetX())
                    utm_srs = osr.SpatialReference()
                    utm_srs.ImportFromEPSG(epsg)
                    clipped_geom.TransformTo(utm_srs)
                    denominator_value += clipped_geom.GetArea() if ogr.GT_Flatten(clipped_geom.GetGeometryType()) in [ogr.wkbPolygon, ogr.wkbMultiPolygon] else clipped_geom.Length()
                geom = None
                clipped_geom = None
    
    # Calculate the proportion
    if denominator_value == 0.0:
        return 0.0
    else:
        return numerator_value / denominator_value
