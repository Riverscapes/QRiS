import json
import sqlite3
from typing import Dict

from osgeo import ogr

from .db_item import DBItem

STREAM_GAGE_MACHINE_CODE = 'Stream Gages'
STREAM_GAGE_NODE_TAG = 'STREAMGAGES'


class StreamGage(DBItem):
    """Represents USGS stream gages retrieved from NWIS"""

    def __init__(self, id: int, site_code: str, site_name: str, metadata: dict):
        super().__init__('pour_points', id, site_name, metadata)
        self.site_code = site_code
        self.icon = 'watershed'

        # override the default ID column name because this is a spatial table.
        self.id_column_name = 'fid'


def load_stream_gages(curs: sqlite3.Cursor) -> Dict[int, StreamGage]:

    curs.execute('SELECT * FROM stream_gages')
    return {row['fid']: StreamGage(
        row['fid'],
        row['site_code'],
        row['site_name'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}

# def save_pour_point(project_file: str, latitude: float, longitude: float, catchment: dict, name: str, description: str, basin_chars: dict, flow_stats: dict) -> PourPoint:

#     driver = ogr.GetDriverByName('GPKG')
#     dataset = driver.Open(project_file, 1)
#     pour_point_id = None

#     # Save pour point
#     layer = dataset.GetLayerByName('pour_points')
#     featureDefn = layer.GetLayerDefn()
#     outFeature = ogr.Feature(featureDefn)
#     point = ogr.Geometry(ogr.wkbPoint)
#     point.AddPoint(longitude, latitude)
#     outFeature.SetGeometry(point)
#     outFeature.SetField('name', name)
#     outFeature.SetField('latitude', latitude)
#     outFeature.SetField('longitude', longitude)
#     if description is not None and len(description) > 0:
#         outFeature.SetField('description', description)

#     if basin_chars is not None:
#         outFeature.SetField('basin_characteristics', json.dumps(basin_chars))

#     if flow_stats is not None:
#         outFeature.SetField('flow_statistics', json.dumps(flow_stats))

#     out = layer.CreateFeature(outFeature)
#     pour_point_id = outFeature.GetFID()

#     # Save catchment polygon
#     layer = dataset.GetLayerByName('catchments')
#     geojson = catchment['featurecollection'][1]['feature']['features'][0]['geometry']
#     polygon = ogr.CreateGeometryFromJson(json.dumps(geojson))
#     featureDefn = layer.GetLayerDefn()
#     outFeature = ogr.Feature(featureDefn)
#     outFeature.SetGeometry(polygon)
#     outFeature.SetField('pour_point_id', pour_point_id)
#     layer.CreateFeature(outFeature)

#     return PourPoint(pour_point_id, name, longitude, latitude, description, json.dumps(basin_chars), json.dumps(flow_stats))
