"""Methods for generating analysis metrics."""

import os
import math
import json
import sqlite3
from typing import Generator
from decimal import Decimal, InvalidOperation

from osgeo import ogr, gdal, osr

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
    'area_proportion': 'ratio',
    'proportion': 'ratio',
    'elevation': 'distance'
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


def get_dependency_value(metric_params: dict, analysis_params: dict, usage: str) -> float:
    """Resolve a dependency value by usage alias or dependency key.

    The runtime task pre-populates analysis_params['metric_dependencies'] with values keyed
    by usage (when provided in metric_dependencies) and by protocol::metric::version keys.
    """
    dependency_values = analysis_params.get('metric_dependencies', {}) if analysis_params else {}
    if usage in dependency_values:
        return dependency_values[usage]

    for dep in metric_params.get('metric_dependencies', []):
        if dep.get('usage') != usage:
            continue
        machine_code = dep.get('metric_id_ref')
        if not machine_code:
            continue
        protocol_code = dep.get('protocol_machine_code_ref', '')
        version = dep.get('version')

        exact_key = f'{protocol_code}::{machine_code}::{version}' if version is not None else None
        loose_key = f'{protocol_code}::{machine_code}::'

        if version is not None:
            version_str = str(version).strip()
            normalized_version = None
            if version_str != '':
                try:
                    normalized_version = format(Decimal(version_str).normalize(), 'f')
                    if '.' in normalized_version:
                        normalized_version = normalized_version.rstrip('0').rstrip('.')
                except (InvalidOperation, ValueError):
                    normalized_version = version_str
            if normalized_version is not None:
                normalized_exact_key = f'{protocol_code}::{machine_code}::{normalized_version}'
            else:
                normalized_exact_key = None
        else:
            normalized_exact_key = None

        if exact_key is not None and exact_key in dependency_values:
            return dependency_values[exact_key]
        if normalized_exact_key is not None and normalized_exact_key in dependency_values:
            return dependency_values[normalized_exact_key]
        if loose_key in dependency_values:
            return dependency_values[loose_key]

    raise MetricInputMissingError(
        f"Missing dependency value for usage '{usage}'. Ensure a metric dependency provides this usage and has been computed first."
    )

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

def get_dce_layer_source(project_file: str, machine_code: str, event_id: int = None) -> tuple[str, int]:

    with sqlite3.connect(project_file, timeout=10.0) as conn:
        c = conn.cursor()
        layer_data = None
        if event_id is not None:
            # Scope lookup to the specific event's layer assignments when available.
            # Some older/minimal project DBs may not have event_layers yet.
            try:
                c.execute("""
                    SELECT l.id, l.geom_type
                    FROM event_layers el
                    JOIN layers l ON l.id = el.layer_id
                    WHERE el.event_id = ? AND l.fc_name = ?
                """, (event_id, machine_code))
                layer_data = c.fetchone()
            except sqlite3.OperationalError:
                layer_data = None
        if layer_data is None:
            # Fallback: unscoped lookup (used when event_id not supplied)
            c.execute('SELECT id, geom_type FROM layers WHERE fc_name = ?', (machine_code,))
            layer_data = c.fetchone()
        if layer_data is None:
            return None, None
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
            layer_id, layer_name = get_dce_layer_source(project_file, metric_layer['layer_id_ref'], event_id)
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


def _get_surface_raster_path(project_file: str, metric_params: dict, analysis_params: dict) -> str:
    surface: Raster = None
    for input_param in metric_params.get('inputs', []):
        if input_param.get('usage', None) == 'surface':
            surface = analysis_params.get(input_param.get('input_ref', None), None)
            break
    if surface is None:
        raise MetricInputMissingError('Surface raster input is required for this metric.')

    raster_layer = os.path.join(os.path.dirname(project_file), surface.path)
    if not os.path.exists(raster_layer):
        raise MetricInputMissingError(f'Expected raster layer {raster_layer} does not exist.')
    return raster_layer


def _get_metric_lines(
    project_file: str,
    sample_frame_feature_id: int,
    event_id: int,
    metric_params: dict,
    analysis_params: dict,
    clip_to_sample_frame: bool,
) -> list:
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

            if clip_to_sample_frame:
                if not geom.Intersects(sample_frame_geom):
                    continue
                geom = geom.Intersection(sample_frame_geom)

            if geom is None or geom.IsEmpty():
                continue

            if ogr.GT_Flatten(geom.GetGeometryType()) in [ogr.wkbLineString, ogr.wkbMultiLineString]:
                line_geoms.append(geom)

    return line_geoms


def _merge_lines(line_geoms: list) -> ogr.Geometry:
    if len(line_geoms) < 1:
        return None

    union_geom = line_geoms[0].Clone()
    for g in line_geoms[1:]:
        union_geom = union_geom.Union(g)

    # Try to make endpoint extraction deterministic.
    try:
        merged = union_geom.LineMerge()
        if merged is not None and not merged.IsEmpty():
            union_geom = merged
    except Exception:
        raise MetricCalculationError('Error during line merging for sinuosity calculation.')

    if ogr.GT_Flatten(union_geom.GetGeometryType()) == ogr.wkbMultiLineString and union_geom.GetGeometryCount() == 1:
        union_geom = union_geom.GetGeometryRef(0).Clone()

    return union_geom


def _line_endpoints(union_geom: ogr.Geometry) -> tuple:
    geom_type = ogr.GT_Flatten(union_geom.GetGeometryType())
    if geom_type == ogr.wkbLineString:
        if union_geom.GetPointCount() < 2:
            raise MetricCalculationError('Line geometry does not have enough points.')
        start_pt = union_geom.GetPoint(0)
        end_pt = union_geom.GetPoint(union_geom.GetPointCount() - 1)
        return start_pt, end_pt

    if geom_type == ogr.wkbMultiLineString:
        if union_geom.GetGeometryCount() < 1:
            raise MetricCalculationError('MultiLine geometry has no line parts.')
        first_line = union_geom.GetGeometryRef(0)
        last_line = union_geom.GetGeometryRef(union_geom.GetGeometryCount() - 1)
        if first_line is None or last_line is None:
            raise MetricCalculationError('Unable to read line parts for endpoint sampling.')
        start_pt = first_line.GetPoint(0)
        end_pt = last_line.GetPoint(last_line.GetPointCount() - 1)
        return start_pt, end_pt

    raise MetricCalculationError('Unioned geometry is not a line.')


def _sample_raster_value(raster_path: str, x: float, y: float, point_srs: osr.SpatialReference = None) -> float:
    ds = gdal.Open(raster_path)
    if ds is None:
        raise MetricCalculationError(f'Unable to open raster: {raster_path}')

    raster_srs = None
    proj_wkt = ds.GetProjection()
    if proj_wkt:
        raster_srs = osr.SpatialReference()
        raster_srs.ImportFromWkt(proj_wkt)

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(x, y)
    if point_srs is not None:
        point.AssignSpatialReference(point_srs)

    if raster_srs is not None and point_srs is not None and not point_srs.IsSame(raster_srs):
        point.TransformTo(raster_srs)

    gt = ds.GetGeoTransform()
    if gt is None:
        raise MetricCalculationError('Raster has no geotransform.')
    if abs(gt[2]) > 1.0e-12 or abs(gt[4]) > 1.0e-12:
        raise MetricCalculationError('Raster rotation is not supported for endpoint sampling.')

    px = int((point.GetX() - gt[0]) / gt[1])
    py = int((point.GetY() - gt[3]) / gt[5])
    if px < 0 or py < 0 or px >= ds.RasterXSize or py >= ds.RasterYSize:
        raise MetricCalculationError('Sample point falls outside raster bounds.')

    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray(px, py, 1, 1)
    if arr is None:
        raise MetricCalculationError('Unable to read raster cell value.')
    value = float(arr[0][0])

    nodata = band.GetNoDataValue()
    if nodata is not None and value == nodata:
        raise MetricCalculationError('Sampled raster cell is NoData.')

    return value


def _endpoint_elevations(
    project_file: str,
    sample_frame_feature_id: int,
    event_id: int,
    metric_params: dict,
    analysis_params: dict,
    clip_to_sample_frame: bool,
) -> tuple:
    line_geoms = _get_metric_lines(
        project_file,
        sample_frame_feature_id,
        event_id,
        metric_params,
        analysis_params,
        clip_to_sample_frame,
    )
    if len(line_geoms) < 1:
        raise MetricInputMissingError('No line features found for endpoint elevation sampling.')

    # Capture SRS from source lines before merging, since LineMerge / Union may strip it.
    line_srs = None
    for g in line_geoms:
        srs = g.GetSpatialReference()
        if srs is not None:
            line_srs = srs
            break

    union_geom = _merge_lines(line_geoms)
    if union_geom is None or union_geom.IsEmpty():
        raise MetricInputMissingError('No valid line geometry available for endpoint elevation sampling.')

    start_pt, end_pt = _line_endpoints(union_geom)
    if line_srs is None:
        line_srs = union_geom.GetSpatialReference()
    raster_path = _get_surface_raster_path(project_file, metric_params, analysis_params)

    upstream = _sample_raster_value(raster_path, start_pt[0], start_pt[1], line_srs)
    downstream = _sample_raster_value(raster_path, end_pt[0], end_pt[1], line_srs)
    return upstream, downstream


def count(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict) -> int:
    """Count the number of features in the specified layers that intersect the mask feature.
    
        CalculationID: 1
    """
    
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)

    total_feature_count = 0
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', [])
    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            continue
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
            total_feature_count += feature_count

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
            epsg = get_utm_zone_epsg(geom.Centroid().GetX())
            utm_srs = osr.SpatialReference()
            utm_srs.ImportFromEPSG(epsg)
            usage = str(metric_layer.get('usage', '')).lower()
            clip_input_to_sample_frame = usage.startswith('sample_frame')
            if metric_layer.get('input_ref') is not None and not clip_input_to_sample_frame:
                # Input (riverscape/profile) metrics: default is full input geometry.
                geom.TransformTo(utm_srs)
                total_length += geom.Length()
            elif geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                clipped_geom.TransformTo(utm_srs)
                total_length += clipped_geom.Length()
            geom = None

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

    # Explicit sample-frame mode: report area of the sample-frame polygon itself.
    if any(str(ml.get('usage', '')).lower() == 'sample_frame_area' for ml in metric_layers):
        epsg = get_utm_zone_epsg(sample_frame_geom.Centroid().GetX())
        utm_srs = osr.SpatialReference()
        utm_srs.ImportFromEPSG(epsg)
        proj_sample_frame_geom = sample_frame_geom.Clone()
        proj_sample_frame_geom.TransformTo(utm_srs)
        return proj_sample_frame_geom.GetArea()

    for metric_layer in metric_layers:
        if metric_layer.get('usage', None) == 'normalization':
            continue
        for feature in get_metric_layer_features(project_file, metric_layer, event_id, sample_frame_geom, analysis_params):
            if feature is None:
                continue
            geom: ogr.Geometry = feature.GetGeometryRef().Clone()
            if not geom.IsValid():
                geom = geom.MakeValid()
            epsg = get_utm_zone_epsg(geom.Centroid().GetX())
            utm_srs = osr.SpatialReference()
            utm_srs.ImportFromEPSG(epsg)
            usage = str(metric_layer.get('usage', '')).lower()
            clip_input_to_sample_frame = usage.startswith('sample_frame')
            if metric_layer.get('input_ref') is not None and not clip_input_to_sample_frame:
                # Input (riverscape/profile) metrics: default is full input geometry.
                geom.TransformTo(utm_srs)
                total_area += geom.GetArea()
            elif geom.Intersects(sample_frame_geom):
                clipped_geom: ogr.Geometry = geom.Intersection(sample_frame_geom)
                clipped_geom.TransformTo(utm_srs)
                total_area += clipped_geom.GetArea()
            geom = None

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

    # Capture SRS from source lines before union; OGR set operations may strip SRS.
    source_utm_srs = None
    for g in line_geoms:
        srs = g.GetSpatialReference()
        if srs is not None:
            source_utm_srs = srs
            break

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
    utm_srs = union_geom.GetSpatialReference() or source_utm_srs
    point_start = ogr.Geometry(ogr.wkbPoint)
    point_start.AssignSpatialReference(utm_srs)
    point_start.AddPoint(start_pt[0], start_pt[1])
    point_end = ogr.Geometry(ogr.wkbPoint)
    point_end.AssignSpatialReference(utm_srs)
    point_end.AddPoint(end_pt[0], end_pt[1])

    buffer_start = point_start.Buffer(10)
    buffer_end = point_end.Buffer(10)
    # Buffer may also drop SRS — re-assign to be safe before zonal stats does its own transform.
    if utm_srs is not None:
        buffer_start.AssignSpatialReference(utm_srs)
        buffer_end.AssignSpatialReference(utm_srs)

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
    metric_dependencies = metric_params.get('metric_dependencies', []) if metric_params else []
    metric_layers = metric_params.get('dce_layers', []) + metric_params.get('inputs', []) if metric_params else []

    # If no spatial inputs are provided and metric dependencies are configured,
    # compute the proportion directly from dependency values.
    if len(metric_layers) == 0 and len(metric_dependencies) > 0:
        numerator_value = get_dependency_value(metric_params, analysis_params, 'numerator')
        denominator_value = get_dependency_value(metric_params, analysis_params, 'denominator')
        if denominator_value == 0:
            return 0.0
        return numerator_value / denominator_value
    
    # Initialize the sample frame geometry
    sample_frame_geom = get_sample_frame_geom(project_file, sample_frame_feature_id)
    
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


def elevation(project_file: str, sample_frame_feature_id: int, event_id: int, metric_params: dict, analysis_params: dict):
    """Endpoint elevation sampler with mode encoded in centerline input usage.

    Supported centerline usage values:
    - profile_upstream / profile_downstream / profile_difference
    - sample_frame_upstream / sample_frame_downstream / sample_frame_difference
    """
    mode = 'profile_difference'
    for input_param in metric_params.get('inputs', []):
        if input_param.get('input_ref') != 'centerline':
            continue
        usage = str(input_param.get('usage', '')).strip().lower()
        if usage in {
            'profile_upstream',
            'profile_downstream',
            'profile_difference',
            'sample_frame_upstream',
            'sample_frame_downstream',
            'sample_frame_difference',
        }:
            mode = usage
            break

    clip_to_sample_frame = mode.startswith('sample_frame_')
    upstream, downstream = _endpoint_elevations(
        project_file,
        sample_frame_feature_id,
        event_id,
        metric_params,
        analysis_params,
        clip_to_sample_frame,
    )

    if mode.endswith('upstream'):
        return upstream
    if mode.endswith('downstream'):
        return downstream
    return downstream - upstream
