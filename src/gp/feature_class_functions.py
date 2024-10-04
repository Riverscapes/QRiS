import os

from osgeo import ogr
from osgeo import osr
from shapely.wkb import loads as wkbload, dumps as wkbdumps
from osgeo.gdal import Warp, WarpOptions
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsVectorLayer, QgsGeometry

from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayer, QgsWkbTypes
from qgis.utils import iface

from ..model.db_item import DBItem
from ..model.profile import Profile
from ..model.project import Project

from typing import Tuple

def check_geometry_type(path) -> int:

    ds = ogr.Open(path)
    layer = ds.GetLayer(0)
    return layer.GetGeomType()


def flip_line_geometry(project: Project, profile: Profile):

    if profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE:
        layer_name = 'profile_centerlines'
    else:
        layer_name = 'profile_features'

    feature_layer = QgsVectorLayer(f'{project.project_file}|layername={layer_name}')
    feature_layer.setSubsetString(f'profile_id = {profile.id}')
    feature_layer.startEditing()
    feats = feature_layer.getFeatures()
    for feat in feats:
        fid = feat.id()
        pts = feat.geometry().asPolyline()
        pts.reverse()
        out_geom = QgsGeometry.fromPolylineXY(pts)
        feature_layer.changeGeometry(fid, out_geom)
    feature_layer.commitChanges()


def layer_path_parser(path: str) -> Tuple[str, str, object]:
    """
    Parse a layer path into a path, layer name, and identifier (for ogr GetLayer).
    """

    if os.path.splitext(path)[1].lower() == ".shp":
        return path, os.path.splitext(os.path.basename(path))[0], 0
    elif ".gpkg|layername=" in path:
        path, layer_name = path.split('|layername=')
        return path, layer_name, layer_name
    elif ".gdb|layername=" in path:
        path, layer_name = path.split('|layername=')
        return path, layer_name, layer_name
    else:
        # this represents an in-memory layer
        vl = QgsVectorLayer(path)
        return path, vl.name(), "memory"


def import_existing(source_path: str, dest_path: str, dest_layer_name: str, output_id: int, output_id_field: str, attributes: dict = {}, clip_mask: tuple = None) -> None:
    """
    Copy the features from a source feature class to a destination mask feature class.
    The mask record must already exist. The attributes is a dictionary of source column
    names keyed to destination column names. If not None then these attributes will be copied in
    """

    ogr.UseExceptions()

    if os.path.splitext(source_path)[1].lower() == ".shp":
        src_path = source_path
        src_layer_name = None
    else:
        src_path, src_layer_name = source_path.split('|layername=')
    src_dataset: ogr.DataSource = ogr.Open(src_path)
    src_layer: ogr.Layer = src_dataset.GetLayer(src_layer_name if src_layer_name is not None else 0)
    src_srs = src_layer.GetSpatialRef()
    fid_field_name = src_layer.GetFIDColumn()

    gpkg_driver: ogr.Driver = ogr.GetDriverByName('GPKG')
    dst_dataset: ogr.DataSource = gpkg_driver.Open(dest_path, 1)
    dst_layer: ogr.Layer = dst_dataset.GetLayerByName(dest_layer_name)
    dst_srs = dst_layer.GetSpatialRef()
    dst_layer_def = dst_layer.GetLayerDefn()

    clip_geom:ogr.Geometry = None
    if clip_mask is not None:
        clip_layer: ogr.Layer = dst_dataset.GetLayer(clip_mask[0])
        clip_layer.SetAttributeFilter(f'{clip_mask[1]} = {clip_mask[2]}')
        clip_feat: ogr.Feature = clip_layer.GetNextFeature()
        clip_geom = clip_feat.GetGeometryRef()

    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    feats = 0
    src_feature: ogr.Feature = None
    for src_feature in src_layer:
        geom:ogr.Geometry = src_feature.GetGeometryRef()
        geom.Transform(transform)
        if clip_geom is not None:
            geom = clip_geom.Intersection(geom)
            if geom.IsEmpty() or geom is None:
                continue
            if geom.GetGeometryType() in [ogr.wkbPolygon, ogr.wkbMultiPolygon] and geom.GetArea() == 0.0:
                continue
            if geom.GetGeometryType() in [ogr.wkbLineString, ogr.wkbMultiLineString] and geom.Length() == 0.0:
                continue

        dst_feature = ogr.Feature(dst_layer_def)
        dst_feature.SetGeometry(geom)
        dst_feature.SetField(output_id_field, output_id)
        for src_field, dst_field in attributes.items():
            # Retrieve the field value differently if the feature ID is being used
            value = str(src_feature.GetFID()) if src_field == fid_field_name else src_feature.GetField(src_field)
            dst_feature.SetField(dst_field, value)

        err = dst_layer.CreateFeature(dst_feature)
        dst_feature = None
        feats += 1

    src_dataset = None
    dst_dataset = None

    if feats == 0:
        raise Exception("No features were imported. Check that the source and destination coordinate systems are the same and that the source and aoi mask geometries intersect.")


def get_field_names(path: str) -> Tuple[list, list]:

    path, _name, identifier = layer_path_parser(path)

    ds = ogr.Open(path)
    layer = ds.GetLayer(identifier)
    layer_defintion = layer.GetLayerDefn()
    field_names = []
    field_types = []
    for i in range(layer_defintion.GetFieldCount()):
        field_defintion = layer_defintion.GetFieldDefn(i)
        field_names.append(field_defintion.GetName())
        field_types.append(field_defintion.GetTypeName())
    return field_names, field_types


def get_field_values(path: str, field_name: str) -> list:

    path, _name, identifier = layer_path_parser(path)

    ds = ogr.Open(path)
    layer = ds.GetLayer(identifier)
    layer_defintion = layer.GetLayerDefn()
    field_index = layer_defintion.GetFieldIndex(field_name)
    field_values = []
    for feature in layer:
        value = feature.GetField(field_index)
        if value not in field_values:
            field_values.append(value)
    return field_values


def browse_raster(parent, description: str) -> str:
    # https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
    frm_browse = QgsDataSourceSelectDialog(parent=parent, setFilterByLayerType=True, layerType=QgsMapLayer.RasterLayer)
    frm_browse.setDescription(description)

    frm_browse.exec()
    uri = frm_browse.uri()

    if uri is not None and uri.isValid():
        # if uri extension is .vrt then it is a virtual raster and cannot be used
        vrt_ext = os.path.splitext(uri.uri)[1].lower()
        if vrt_ext == '.vrt':
            QMessageBox.warning(parent, 'Invalid Raster',
                                f'The raster is a virtual raster and cannot be used. Please select a different raster.')
            return None
        return uri.uri

    return None


def browse_vector(parent, description: str, geometry_type: QgsWkbTypes.GeometryType) -> str:
    """
    https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
    https://api.qgis.org/api/classQgsWkbTypes.html#a60e72c2f73cb07fdbcdbc2d5068b5d9c

    QgsWkbTypes.GeometryType.PointGeometry
    QgsWkbTypes.GeometryType.LineGeometry
    QgsWkbTypes.GeometryType.PolygonGeometry
    QgsWkbTypes.GeometryType.UnknownGeometry
    QgsWkbTypes.GeometryType.NullGeometry
    """

    frm_browse = QgsDataSourceSelectDialog(parent=parent, setFilterByLayerType=True, layerType=QgsMapLayer.VectorLayer)
    frm_browse.setDescription(description)

    frm_browse.exec()
    uri = frm_browse.uri()
    if uri is not None and uri.isValid():
        layer = QgsVectorLayer(uri.uri, '', 'ogr')
        if geometry_type is not None and geometry_type != layer.geometryType():
            QMessageBox.warning(parent, 'Invalid Geometry Type',
                                f'The layer is of geometry type {QgsWkbTypes.geometryDisplayString(layer.geometryType())} but must be of type {QgsWkbTypes.geometryDisplayString(geometry_type)}.')
            return None

        return uri.uri

    return None
