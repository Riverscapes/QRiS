import os
import json
import numpy as np
import math
import osgeo
from osgeo import ogr, gdal, osr
from shapely.wkb import load, loads as wkbload, dumps as wkbdumps
from osgeo import gdal
from shapely.geometry import mapping
from .zonal_statistics import zonal_statistics


class Metrics:

    def __init__(self, project_file: str, mask_id: int, layers: list):

        self.config = {'vector': {}, 'raster': {}}
        self.project_file = project_file
        self.mask_id = mask_id
        self.layers = layers
        self.metrics = {}
        self.polygons, self.utm_epsg = self.load_polygons(project_file, mask_id)
        # print(json.dumps(mapping(self.polygons[2]['geometry'])))

    def load_polygons(self, project_file: str, mask_id: int) -> dict:

        driver = ogr.GetDriverByName("GPKG")
        ds = driver.Open(project_file)
        layer = ds.GetLayerByName('mask_features')
        layer.SetAttributeFilter(f'mask_id = {mask_id}')
        src_srs = layer.GetSpatialRef()

        # Target transform to most appropriate UTM zone
        utm_transform = None
        epsg = None

        polygons = {}
        for feature in layer:
            geom = feature.GetGeometryRef()

            if utm_transform is None:
                temp_temp = geom.Clone()

                # Temporarily transform to WGS84 to determine best UTM zone
                wgs_srs = osr.SpatialReference()
                wgs_srs.ImportFromEPSG(4326)
                wgs_transform = osr.CoordinateTransformation(src_srs, wgs_srs)
                temp_temp.Transform(wgs_transform)

                epsg = self.get_utm_zone_epsg(geom.Centroid().GetX())
                utm_srs = osr.SpatialReference()
                utm_srs.ImportFromEPSG(epsg)
                utm_transform = osr.CoordinateTransformation(src_srs, utm_srs)

            geom.Transform(utm_transform)

            if geom.IsMeasured() > 0 or geom.Is3D() > 0:
                geom.FlattenTo2D()
            polygons[feature.GetFID()] = {
                'geometry': wkbload(bytes(geom.ExportToWkb())),
                'display_label': feature.GetField('display_label')
            }

        layer = None
        ds = None

        if len(polygons) < 1:
            raise Exception('Mask Feature Class is empty. No polygons loaded.')

        return polygons, epsg

    def get_utm_zone_epsg(self, longitude: float) -> int:
        """Really crude EPSG lookup method

        Args:
            longitude (float): [description]

        Returns:
            int: [description]
        """
        zone_number = math.floor((180.0 + longitude) / 6.0)
        epsg = 26901 + zone_number
        return epsg

    def run(self) -> dict:

        metrics = {}
        for layer in self.layers:
            if layer['type'] == 'vector':
                metrics[layer['name']] = self.process_vector(layer)
            else:
                metrics[layer['name']] = self.process_raster(layer)

        return metrics

    def process_vector(self, layer_def):

        if '|' in layer_def['url']:
            parts = layer_def['url'].split('|')
            ds = ogr.Open(parts[0])
            layer_name = parts[1].replace('layername=', '')
            layer = ds.GetLayerByName(layer_name)
        else:
            ds = ogr.Open(layer_def['url'])
            layer = ds.GetLayer(0)
        src_srs = layer.GetSpatialRef()

        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(self.utm_epsg)
        transform_src_to_utm = osr.CoordinateTransformation(src_srs, dst_srs)

        # Used for transforming polygons onto the layer SRS for spatial filter
        transform_utm_to_src = osr.CoordinateTransformation(dst_srs, src_srs)

        metrics = {}
        for polygon_id, polygon_data in self.polygons.items():
            polygon = polygon_data['geometry']
            polygon_geom = ogr.CreateGeometryFromWkb(polygon.wkb)
            polygon_geom.Transform(transform_utm_to_src)

            polygon_metrics = {'count': 0}
            layer.SetSpatialFilter(polygon_geom)
            for feature in layer:
                geom = feature.GetGeometryRef()
                geom.Transform(transform_src_to_utm)

                if geom.IsMeasured() > 0 or geom.Is3D() > 0:
                    geom.FlattenTo2D()

                shape = wkbload(bytes(geom.ExportToWkb()))
                if polygon.intersects(shape):
                    inter = polygon.intersection(shape)
                    polygon_metrics['count'] += 1

                    if inter.geom_type == 'LineString' or inter.geom_type == 'MultiLineString':
                        polygon_metrics['length'] = inter.length if 'length' not in polygon_metrics else inter.length + polygon_metrics['length']
                    elif inter.geom_type == 'Polygon' or inter.geom_type == 'MultiPolygon':
                        polygon_metrics['area'] = inter.area if 'area' not in polygon_metrics else inter.area + polygon_metrics['area']

            metrics[polygon_id] = polygon_metrics

        return metrics

    def process_raster(self, layer_def):

        raster = gdal.Open(layer_def['url'])
        # src_srs = raster.GetProjection()
        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(raster.GetProjection())

        # Handle GDAL axis mapping issues
        # https://github.com/OSGeo/gdal/issues/1546
        if int(osgeo.__version__[0]) >= 3:
            # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
            src_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

        raster = None

        # Used for transforming polygons onto the raster  SRS
        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(self.utm_epsg)
        transform_utm_to_src = osr.CoordinateTransformation(dst_srs, src_srs)

        results = {}

        for polygon_id, polygon_data in self.polygons.items():
            polygon = polygon_data['geometry']
            polygon_geom = ogr.CreateGeometryFromWkb(polygon.wkb)
            polygon_geom.Transform(transform_utm_to_src)
            results[polygon_id] = zonal_statistics(layer_def['url'], polygon_geom)

        return results

    # def categorical_raster_metrics(self, dataset_name, raster_path):

    #     cell_area = get_raster_cell_area(raster_path)

    #     cats = {key: {} for key in self.polygons.keys()}
    #     with rasterio.open(raster_path) as src:

    #         for poly_id, polygon in self.polygons.items():

    #             raw_raster, _out_transform = mask(src, [polygon], crop=True)
    #             # mask_raster = np.ma.masked_values(raw_raster, src.nodata)

    #             for val in np.unique(raw_raster):
    #                 if val != src.nodata:
    #                     cats[poly_id][str(val)] = {'area': np.count_nonzero(raw_raster == val) * cell_area,
    #                                                'count': np.count_nonzero(raw_raster == val)}

    #     for key in cats.keys():
    #         self.metrics['project']['huc12'][key]['metrics']['raster']['categorical'].append({dataset_name: {'cellSize': np.sqrt(cell_area), 'categories': cats[key]}})
