import json
import sqlite3
from osgeo import ogr

from .db_item import DBItem

POUR_POINTS_MACHINE_CODE = 'Pour Points'
CATCHMENTS_MACHINE_CODE = 'CATCHMENTS'


class PourPoint(DBItem):
    """Represents points on the map that  the usser has clicked on and delineated
    upstream catchments using stream statss"""

    def __init__(self, id: int, name: str, latitude: float, longitude: float, description: str, basin_chars: str, flow_stats: str):
        super().__init__('pour_points', id, name)
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.basin_chars = json.loads(basin_chars) if basin_chars is not None else None
        self.flow_stats = json.loads(flow_stats) if flow_stats is not None else None
        self.icon = 'watershed'

        # override the default ID column name because this is a spatial table.
        self.id_column_name = 'fid'

    def update(self, db_path: str, name: str, description: str) -> None:
        """ Pour point is a feature class therefore need to use ogr to edit features.
        Can't use direct SQL
        """

        # Don't forget to include the write access modifier
        src_dataset = ogr.Open(db_path, 1)
        src_layer = src_dataset.GetLayer(self.db_table_name)
        src_layer.SetAttributeFilter(f'fid={self.id}')

        for feature in src_layer:
            feature.SetField('name', name)
            if description is None or len(description) < 1:
                feature.SetFieldNull('description')
            else:
                feature.SetField('description', description)
            src_layer.SetFeature(feature)

        self.name = name
        self.description = description

        feature = None
        src_layer = None
        src_dataset = None


def load_pour_points(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM pour_points')
    return {row['fid']: PourPoint(
        row['fid'],
        row['name'],
        row['latitude'],
        row['longitude'],
        row['description'],
        row['basin_characteristics'],
        row['flow_statistics']
    ) for row in curs.fetchall()}


def save_pour_point(project_file: str, latitude: float, longitude: float, catchment: dict, name: str, description: str, basin_chars: dict, flow_stats: dict) -> PourPoint:

    driver = ogr.GetDriverByName('GPKG')
    dataset = driver.Open(project_file, 1)
    pour_point_id = None

    # Save pour point
    layer = dataset.GetLayerByName('pour_points')
    featureDefn = layer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(longitude, latitude)
    outFeature.SetGeometry(point)
    outFeature.SetField('name', name)
    outFeature.SetField('latitude', latitude)
    outFeature.SetField('longitude', longitude)
    if description is not None and len(description) > 0:
        outFeature.SetField('description', description)

    if basin_chars is not None:
        outFeature.SetField('basin_characteristics', json.dumps(basin_chars))

    if flow_stats is not None:
        outFeature.SetField('flow_statistics', json.dumps(flow_stats))

    out = layer.CreateFeature(outFeature)
    pour_point_id = outFeature.GetFID()

    # Save catchment polygon
    layer = dataset.GetLayerByName('catchments')
    geojson = catchment['featurecollection'][1]['feature']['features'][0]['geometry']
    polygon = ogr.CreateGeometryFromJson(json.dumps(geojson))
    featureDefn = layer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    outFeature.SetGeometry(polygon)
    outFeature.SetField('pour_point_id', pour_point_id)
    layer.CreateFeature(outFeature)

    return PourPoint(pour_point_id, name, longitude, latitude, description, json.dumps(basin_chars), json.dumps(flow_stats))
