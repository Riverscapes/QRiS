"""
Raster zonal statistics for a polygon.

Code adapted from Konrad Hafen's tutorial here
https://opensourceoptions.com/blog/zonal-statistics-algorithm-with-python-in-4-steps/

Note that the OGR polygon passed in MUST be in the same coordinate reference system
as the raster dataset. It is the caller's responsibility to reproject it before
calling this function.

Other Resources:
https://www.gis.usu.edu/~chrisg/python/2009/lectures/ospy_slides4.pdf
"""

import osgeo
from osgeo import gdal, ogr, osr
import numpy as np

TEMP_FEATURE_CLASS_NAME = 'temp_fc'


def zonal_statistics(raster_path: str, geom: ogr.Geometry) -> dict:
    """
    raster_path: Full path to existing raster for which zonal statistics are needed
    geom: OGR polygon geometry that defines the required zone. MUST BE IN SAME SRS as raster!!!
    """

    raster_ds = gdal.Open(raster_path)
    raster_gt = raster_ds.GetGeoTransform()
    raster_nd = raster_ds.GetRasterBand(1).GetNoDataValue()

    ogr_mem_driver = ogr.GetDriverByName('MEM') or ogr.GetDriverByName('Memory')
    gdl_mem_driver = gdal.GetDriverByName('MEM')

    # Attempt to delete existing feature class. This now
    # throws an exception on latest QGIS. But there is no
    # way to check if the feature class already exists because
    # it is an in-memory data source
    try:
        ogr_mem_driver.DeleteDataSource(TEMP_FEATURE_CLASS_NAME)
    except Exception:
        print('Failed to delete in-memory data source')

    # Create in-memory feature class that contains the polygon
    ogr_mem_ds = ogr_mem_driver.CreateDataSource(TEMP_FEATURE_CLASS_NAME)
    ogr_mem_lyr = ogr_mem_ds.CreateLayer('polygons', None, ogr.wkbPolygon)
    featureDefn = ogr_mem_lyr.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    out_geom = geom.Clone()
    out_geom.TransformTo(raster_ds.GetSpatialRef())
    out_geom.MakeValid()
    outFeature.SetGeometry(out_geom)
    ogr_mem_lyr.CreateFeature(outFeature)

    # Set bounding box as intersection of raster extent and polygon extent
    r_minX = raster_gt[0]
    r_maxY = raster_gt[3]
    r_maxX = r_minX + raster_gt[1] * raster_ds.RasterXSize
    r_minY = r_maxY + raster_gt[5] * raster_ds.RasterYSize
    (g_minX, g_maxX, g_minY, g_maxY) = out_geom.GetEnvelope()
    extents = (max([g_minX, r_minX]), min([g_maxX, r_maxX]), max([g_minY, r_minY]), min([g_maxY, r_maxY]))

    # Convert the polygon bounding box to cell offset coordinates
    offsets = boundingBoxToOffsets(extents, raster_gt)
    
    # Clamp the offsets to the raster dimensions to avoid out of bounds errors
    # on exact edge alignments
    offsets[1] = min(offsets[1], raster_ds.RasterYSize) # row2
    offsets[3] = min(offsets[3], raster_ds.RasterXSize) # col2

    # Calculate the new geotransform for the polygonized raster
    new_geot = geotFromOffsets(offsets[0], offsets[2], raster_gt)

    # Create the empty raster for the rasterized polygon in memory
    # and set the geotransform from the rasterized polygon
    tr_ds = gdl_mem_driver.Create('', offsets[3] - offsets[2], offsets[1] - offsets[0], 1, gdal.GDT_Byte)
    tr_ds.SetGeoTransform(new_geot)

    # Rasterize the polygon and read it into a NumPy array
    gdal.RasterizeLayer(tr_ds, [1], ogr_mem_lyr, burn_values=[1])
    tr_array = tr_ds.ReadAsArray()

    # read the input rasterfor the location that corresponds to the rasterized polygon
    r_array = raster_ds.GetRasterBand(1).ReadAsArray(
        offsets[2],
        offsets[0],
        offsets[3] - offsets[2],
        offsets[1] - offsets[0])

    results = {'minimum': None, 'maximum': None, 'mean': None, 'median': None, 'std': None, 'sum': None, 'count': None}
    if r_array is not None:
        maskarray = np.ma.MaskedArray(r_array, mask=np.logical_or(r_array == raster_nd, np.logical_not(tr_array)))
        if maskarray is not None:
            results = {
                'minimum': maskarray.min(),
                'maximum': maskarray.max(),
                'mean': maskarray.mean(),
                'median': np.ma.median(maskarray),
                'std': maskarray.std(),
                'sum': maskarray.sum(),
                'count': maskarray.count()
            }

    # Discard the in-memory datasets
    tr_ds = None
    ogr_mem_ds = None
    raster_ds = None 
    return results


def boundingBoxToOffsets(bbox, geot):
    col1 = int((bbox[0] - geot[0]) / geot[1])
    col2 = int((bbox[1] - geot[0]) / geot[1]) + 1
    row1 = int((bbox[3] - geot[3]) / geot[5])
    row2 = int((bbox[2] - geot[3]) / geot[5]) + 1
    return [row1, row2, col1, col2]


def geotFromOffsets(row_offset, col_offset, geot):
    new_geot = [
        geot[0] + (col_offset * geot[1]),
        geot[1],
        0.0,
        geot[3] + (row_offset * geot[5]),
        0.0,
        geot[5]
    ]
    return new_geot


if __name__ == '__main__':

    raster_path = '/Users/philip/GISData/test/dem_hillshade.tif'
    vector_path = '/Users/philip/GISData/test/test_mask.shp'

    raster_ds = gdal.Open(raster_path)
    if raster_ds is None:
        raise Exception(f'Could not open raster: {raster_path}')

    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(raster_ds.GetProjection())

    # Handle GDAL axis mapping issues
    # https://github.com/OSGeo/gdal/issues/1546
    if int(osgeo.__version__[0]) >= 3:
        # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
        raster_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    vector_ds = ogr.Open(vector_path)
    vector_lr = vector_ds.GetLayer()
    vector_srs = vector_lr.GetSpatialRef()
    transform = osr.CoordinateTransformation(vector_srs, raster_srs)
    # x_min, x_max, y_min, y_max = source_layer.GetExtent()

    for feature in vector_lr:
        geom = feature.GetGeometryRef()
        # geom.Transform(transform)
        break

    results = zonal_statistics(raster_path, geom)
    print(results)
