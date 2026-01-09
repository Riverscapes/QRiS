# coding=utf-8
"""Tests for analysis_metrics module."""

import unittest
import os
import sqlite3
import shutil
import tempfile
import sys
from unittest.mock import MagicMock
import math

# --- MOCKING DEPENDENCIES BEFORE IMPORT ---

# Mock QGIS
mock_qgis = MagicMock()
mock_qgis.core = MagicMock()
sys.modules['qgis'] = mock_qgis
sys.modules['qgis.core'] = mock_qgis.core

# Mock PyQt5
mock_pyqt = MagicMock()
mock_pyqt.QtCore = MagicMock()
sys.modules['PyQt5'] = mock_pyqt
sys.modules['PyQt5.QtCore'] = mock_pyqt.QtCore

# Mock internal modules that are hard to load
mock_zonal = MagicMock()
sys.modules['qris_dev.src.gp.zonal_statistics'] = mock_zonal

class MockLayer:
    DCE_LAYER_NAMES = {'Point': 'dce_points',
                      'Linestring': 'dce_lines',
                      'Polygon': 'dce_polygons',
                      'MultiPolygon': 'dce_polygons'}

mock_model_layer = MagicMock()
mock_model_layer.Layer = MockLayer
sys.modules['qris_dev.src.model.layer'] = mock_model_layer

sys.modules['qris_dev.src.model.db_item'] = MagicMock()
sys.modules['qris_dev.src.model.profile'] = MagicMock()
sys.modules['qris_dev.src.model.raster'] = MagicMock()

# --- END MOCKING ---

from osgeo import ogr, osr, gdal

# Enable GDAL/OGR exceptions
gdal.UseExceptions()

# Attempt import
# print(sys.path)
from qris_dev.src.gp.analysis_metrics import area_proportion, count, length, area, sinuosity


class TestAnalysisMetrics(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_file = os.path.join(self.test_dir, 'test_project.gpkg')
        
        driver = ogr.GetDriverByName('GPKG')
        self.ds = driver.CreateDataSource(self.project_file)
        
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326) # WGS84

        # 1. Create Layers
        # Use 2.5D types to avoid warnings about Z mismatch
        self.sample_frame_layer = self.ds.CreateLayer('sample_frame_features', srs, ogr.wkbPolygon25D)
        
        # Valid NAD83 Sample Frame (Oregon/Washington border area)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-122.0, 45.0)
        ring.AddPoint(-122.0, 45.1)
        ring.AddPoint(-121.9, 45.1)
        ring.AddPoint(-121.9, 45.0)
        ring.AddPoint(-122.0, 45.0)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        
        feature = ogr.Feature(self.sample_frame_layer.GetLayerDefn())
        feature.SetGeometry(poly)
        self.sample_frame_layer.CreateFeature(feature)
        self.sample_frame_id = feature.GetFID()

        fd_eid = ogr.FieldDefn('event_id', ogr.OFTInteger)
        fd_elid = ogr.FieldDefn('event_layer_id', ogr.OFTInteger)
        fd_meta = ogr.FieldDefn('metadata', ogr.OFTString)

        self.dce_polygons_layer = self.ds.CreateLayer('dce_polygons', srs, ogr.wkbPolygon25D)
        self.dce_polygons_layer.CreateField(fd_eid)
        self.dce_polygons_layer.CreateField(fd_elid)
        self.dce_polygons_layer.CreateField(fd_meta)
        
        self.dce_lines_layer = self.ds.CreateLayer('dce_lines', srs, ogr.wkbLineString25D)
        self.dce_lines_layer.CreateField(fd_eid)
        self.dce_lines_layer.CreateField(fd_elid)
        self.dce_lines_layer.CreateField(fd_meta)
        
        # 2. Metadata Tables (Must flush first to be safe, or just use separate conn)
        self.ds.FlushCache()
        
        with sqlite3.connect(self.project_file) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
            c.execute("""
                INSERT INTO layers (id, fc_name, geom_type) VALUES 
                (100, 'dce_polygons', 'Polygon'),
                (200, 'dce_points', 'Point'),
                (300, 'dce_lines', 'Linestring')
            """)
            conn.commit()
            
        self.analysis_params = {} 
        self.count_params = {'inputs': [{'layer_id_ref': 'dce_polygons', 'usage': 'input'}]}
        self.area_params = {'inputs': [{'layer_id_ref': 'dce_polygons', 'usage': 'input'}]}
        self.length_params = {'inputs': [{'layer_id_ref': 'dce_lines', 'usage': 'input'}]}
        self.sinuosity_params = {'inputs': [{'layer_id_ref': 'dce_lines', 'usage': 'input'}]}
        self.area_proportion_params = {'inputs': [{'layer_id_ref': 'dce_polygons', 'usage': 'input'}]}

    def tearDown(self):
        if self.ds is not None:
            self.ds = None
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            pass

    def test_area(self):
        feature = ogr.Feature(self.dce_polygons_layer.GetLayerDefn())
        poly = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-122.0, 45.0)
        ring.AddPoint(-122.0, 45.1)
        ring.AddPoint(-121.9, 45.1)
        ring.AddPoint(-121.9, 45.0)
        ring.AddPoint(-122.0, 45.0)
        poly.AddGeometry(ring)
        feature.SetGeometry(poly)
        
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 100)
        self.dce_polygons_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE TO COMMIT
        
        result = area(self.project_file, self.sample_frame_id, 100, self.area_params, self.analysis_params)
        self.assertGreater(result, 1000)

    def test_length(self):
        feature = ogr.Feature(self.dce_lines_layer.GetLayerDefn())
        line = ogr.Geometry(ogr.wkbLineString)
        line.AddPoint(-122.0, 45.05)
        line.AddPoint(-121.9, 45.05)
        feature.SetGeometry(line)
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 300)
        self.dce_lines_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE
        
        result = length(self.project_file, self.sample_frame_id, 100, self.length_params, self.analysis_params)
        self.assertGreater(result, 7000)

    def test_count_polygon(self):
        # 1. Mostly Inside
        feature = ogr.Feature(self.dce_polygons_layer.GetLayerDefn())
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-122.02, 45.0)
        ring.AddPoint(-122.02, 45.1)
        ring.AddPoint(-121.92, 45.1)
        ring.AddPoint(-121.92, 45.0)
        ring.AddPoint(-122.02, 45.0)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        feature.SetGeometry(poly)
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 100)
        self.dce_polygons_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE
        
        result_count = count(self.project_file, self.sample_frame_id, 100, self.count_params, self.analysis_params)
        self.assertEqual(result_count, 1)

    def test_count_polygon_outside(self):
        # 2. Fully Outside
        feature = ogr.Feature(self.dce_polygons_layer.GetLayerDefn())
        ring = ogr.Geometry(ogr.wkbLinearRing)
        # Shift far left
        ring.AddPoint(-123.0, 45.0)
        ring.AddPoint(-123.0, 45.1)
        ring.AddPoint(-122.9, 45.1)
        ring.AddPoint(-122.9, 45.0)
        ring.AddPoint(-123.0, 45.0)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        feature.SetGeometry(poly)
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 100)
        self.dce_polygons_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE
        
        result_count = count(self.project_file, self.sample_frame_id, 100, self.count_params, self.analysis_params)
        self.assertEqual(result_count, 0)

    def test_sinuosity(self):
        feature = ogr.Feature(self.dce_lines_layer.GetLayerDefn())
        line = ogr.Geometry(ogr.wkbLineString)
        # Same horizontal line as test_length (known to work)
        line.AddPoint(-122.0, 45.05)
        line.AddPoint(-121.9, 45.05)
        feature.SetGeometry(line)
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 300)
        self.dce_lines_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE
        
        result_sin = sinuosity(self.project_file, self.sample_frame_id, 100, self.sinuosity_params, self.analysis_params)
        self.assertAlmostEqual(result_sin, 1.0, places=3)

    def test_area_proportion(self):
        feature = ogr.Feature(self.dce_polygons_layer.GetLayerDefn())
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-122.0, 45.0)
        ring.AddPoint(-122.0, 45.1)
        ring.AddPoint(-121.95, 45.1)
        ring.AddPoint(-121.95, 45.0)
        ring.AddPoint(-122.0, 45.0)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        feature.SetGeometry(poly)
        feature.SetField("event_id", 100)
        feature.SetField("event_layer_id", 100)
        self.dce_polygons_layer.CreateFeature(feature)
        
        self.ds = None # CLOSE
        
        result = area_proportion(self.project_file, self.sample_frame_id, 100, self.area_proportion_params, self.analysis_params)
        self.assertAlmostEqual(result, 0.5, places=1)

if __name__ == '__main__':
    unittest.main()
