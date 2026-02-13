"""Tests for zonal_statistics module."""
import unittest
import os
import shutil
import tempfile
import numpy as np
from osgeo import gdal, osr, ogr
gdal.UseExceptions()

# Import the module under test
import sys
# Add the parent directory to sys.path so we can import 'qris_dev' as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from qris_dev.src.gp.zonal_statistics import zonal_statistics

from utilities import get_qgis_app

class TestZonalStatistics(unittest.TestCase):
    
    def setUp(self):
        get_qgis_app()
        gdal.UseExceptions()
        # Create a temp directory
        self.test_dir = tempfile.mkdtemp()
        self.raster_path = os.path.join(self.test_dir, 'test_raster.tif')

        # Create a dummy raster (10x10, all values = 10)
        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(self.raster_path, 10, 10, 1, gdal.GDT_Float32)
        
        # Set GeoTransform (top-left at 0,0, pixel size 1.0)
        # (top_left_x, w_pixel_res, rotation, top_left_y, rotation, n_pixel_res)
        # Note: Standard GIS convention for North-Up images is negative Y resolution
        geotransform = (0, 1, 0, 10, 0, -1)
        ds.SetGeoTransform(geotransform)
        
        # Set Projection (WGS84)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())
        self.wkt = srs.ExportToWkt() # Save WKT for geometry creation
        
        # Write data (fill with 10)
        band = ds.GetRasterBand(1)
        data = np.full((10, 10), 10, dtype=np.float32)
        
        # Introduce some variation for testing
        # Top-left 5x5 quadrant = 20
        # In array coords (row, col). 
        # Rows 0-5 are the "top" (Map Y 10 down to 5)
        # Cols 0-5 are the "left" (Map X 0 up to 5)
        data[0:5, 0:5] = 20 
        
        band.WriteArray(data)
        band.SetNoDataValue(-9999)
        band.FlushCache()
        ds = None # Close dataset

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_zonal_statistics_full_extent(self):
        """Test zonal stats over the entire raster extent."""
        
        # Create a polygon covering the whole raster (0,0 to 10,10)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(0, 0)
        ring.AddPoint(10, 0)
        ring.AddPoint(10, 10)
        ring.AddPoint(0, 10)
        ring.AddPoint(0, 0)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        # Set SRS on geometry to match raster
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.wkt)
        poly.AssignSpatialReference(srs)

        stats = zonal_statistics(self.raster_path, poly)
        
        # Expected:
        # 25 pixels (5x5) have value 20
        # 75 pixels have value 10
        # Total sum = (25 * 20) + (75 * 10) = 500 + 750 = 1250
        # Mean = 1250 / 100 = 12.5
        
        self.assertAlmostEqual(stats['sum'], 1250)
        self.assertAlmostEqual(stats['mean'], 12.5)
        self.assertEqual(stats['count'], 100)
        self.assertEqual(stats['maximum'], 20)
        self.assertEqual(stats['minimum'], 10)

    # def test_zonal_statistics_subset(self):
    #     """Test zonal stats over a subset (the 20s quadrant)."""
        
    #     # Create a polygon covering the top-left quadrant (0,5 to 5,10)
    #     # Note: Raster Y coordinates go from 10 down to 0.
    #     # Top-left in raster coords (0,0) corresponds to map coords (0, 10).
    #     # We want pixels covering map x[0..5], map y[5..10].
        
    #     ring = ogr.Geometry(ogr.wkbLinearRing)
    #     ring.AddPoint(0, 5)
    #     ring.AddPoint(5, 5)
    #     ring.AddPoint(5, 10)
    #     ring.AddPoint(0, 10)
    #     ring.AddPoint(0, 5)
    #     poly = ogr.Geometry(ogr.wkbPolygon)
    #     poly.AddGeometry(ring)

    #     # Set SRS on geometry to match raster
    #     srs = osr.SpatialReference()
    #     srs.ImportFromWkt(self.wkt)
    #     poly.AssignSpatialReference(srs)

    #     stats = zonal_statistics(self.raster_path, poly)
        
    #     # Expected:
    #     # All 25 pixels should be 20.
        
    #     self.assertEqual(stats['count'], 25)
    #     self.assertAlmostEqual(stats['mean'], 20)
    #     self.assertAlmostEqual(stats['sum'], 500)

if __name__ == "__main__":
    unittest.main()
