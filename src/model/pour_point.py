import json
import sqlite3
from osgeo import ogr

from qgis.core import QgsPoint
from .db_item import DBItem
from ..gp.streamstats_api_ import get_streamstats_data, transform_geometry


class PourPoint(DBItem):
    """Represents points on the map that  the usser has clicked on and delineated
    upstream catchments using stream statss"""

    def __init__(self, id: int, name: str, latitude: float, longitude: float, description: str):
        super().__init__('pour_points', id, name)
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.description = description


def load_pour_points(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM pour_points')
    return {row['fid']: PourPoint(
        row['fid'],
        row['name'],
        0,  # row['latitude'],
        0,  # row['longitude'],
        row['description']
    ) for row in curs.fetchall()}


def process_pour_point(project_file: str, raw_map_point: QgsPoint, epsg: int, name, description):

    # The point is in the map data frame display units. Transform to WGS84
    transformed_point = transform_geometry(raw_map_point, epsg, 4326)

    data = get_streamstats_data(transformed_point.y(), transformed_point.x(), False, False, None)
    if data is not None:

        driver = ogr.GetDriverByName('GPKG')
        dataset = driver.Open(project_file, 1)

        # Save pour point
        layer = dataset.GetLayerByName('pour_points')
        featureDefn = layer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(transformed_point.x(), transformed_point.y())
        outFeature.SetGeometry(point)
        outFeature.SetField('name', name)
        if description is not None:
            outFeature.SetField('description', description)
        out = layer.CreateFeature(outFeature)
        pour_point_id = outFeature.GetFID()

        # Save catchment polygon
        layer = dataset.GetLayerByName('catchments')
        geojson = data[0]['featurecollection'][1]['feature']['features'][0]['geometry']
        polygon = ogr.CreateGeometryFromJson(json.dumps(geojson))
        featureDefn = layer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(polygon)
        outFeature.SetField('pour_point_id', pour_point_id)
        layer.CreateFeature(outFeature)

        return PourPoint(pour_point_id, name, transformed_point.x(), transformed_point.y(), description)

    return None
