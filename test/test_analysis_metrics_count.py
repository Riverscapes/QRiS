"""Tests for analysis_metrics count calculation."""
import unittest
import os
import shutil
import tempfile
import json
import sqlite3
import sys
from unittest.mock import MagicMock

# Mock qgis before importing module under test
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()

from osgeo import ogr, osr

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__)) 
plugin_root = os.path.dirname(current_dir) 
parent_root = os.path.dirname(plugin_root) 

if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

# Import after path setup and mocking
from qris_dev.src.gp.analysis_metrics import count

class TestMetricCount(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.gpkg_path = os.path.join(self.test_dir, 'test_project.gpkg')
        
        # Create GPKG
        driver = ogr.GetDriverByName('GPKG')
        ds = driver.CreateDataSource(self.gpkg_path)
        
        # WGS84 Spatial Ref (Project Standard)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326) 
        
        # 1. Create Sample Frame Layer (1x1 degree box for simplicity)
        sf_layer = ds.CreateLayer('sample_frame_features', srs=srs, geom_type=ogr.wkbPolygon)
        sf_layer.CreateField(ogr.FieldDefn('fid', ogr.OFTInteger))
        
        sf_feat = ogr.Feature(sf_layer.GetLayerDefn())
        sf_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        # 10x10 units approx
        ring.AddPoint(0, 0)
        ring.AddPoint(10, 0)
        ring.AddPoint(10, 10)
        ring.AddPoint(0, 10)
        ring.AddPoint(0, 0)
        sf_geom.AddGeometry(ring)
        sf_feat.SetGeometry(sf_geom)
        sf_feat.SetField('fid', 1)
        sf_layer.CreateFeature(sf_feat)
        
        # 2. Create Pools Layer (Polygons)
        # ID 30
        poly_layer = ds.CreateLayer('dce_polygons', srs=srs, geom_type=ogr.wkbPolygon)
        poly_layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        poly_layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        poly_layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))

        # Pool 1: Fully Inside (Area 1)
        # 1,1 to 2,2
        p1 = ogr.Feature(poly_layer.GetLayerDefn())
        g1 = ogr.Geometry(ogr.wkbPolygon)
        r1 = ogr.Geometry(ogr.wkbLinearRing)
        r1.AddPoint(1,1); r1.AddPoint(2,1); r1.AddPoint(2,2); r1.AddPoint(1,2); r1.AddPoint(1,1)
        g1.AddGeometry(r1)
        p1.SetGeometry(g1)
        p1.SetField('event_id', 100)
        p1.SetField('event_layer_id', 30)
        poly_layer.CreateFeature(p1)

        # Pool 2: 50% Inside (Area 1, 0.5 inside)
        # Center on edge x=10. 9.5 to 10.5
        p2 = ogr.Feature(poly_layer.GetLayerDefn())
        g2 = ogr.Geometry(ogr.wkbPolygon)
        r2 = ogr.Geometry(ogr.wkbLinearRing)
        r2.AddPoint(9.5, 1); r2.AddPoint(10.5, 1); r2.AddPoint(10.5, 2); r2.AddPoint(9.5, 2); r2.AddPoint(9.5, 1)
        g2.AddGeometry(r2)
        p2.SetGeometry(g2)
        p2.SetField('event_id', 100)
        p2.SetField('event_layer_id', 30)
        poly_layer.CreateFeature(p2)

        # Pool 3: 40% Inside (Area 1, 0.4 inside)
        # Center on edge x=10. 9.6 to 10.6
        p3 = ogr.Feature(poly_layer.GetLayerDefn())
        g3 = ogr.Geometry(ogr.wkbPolygon)
        r3 = ogr.Geometry(ogr.wkbLinearRing)
        r3.AddPoint(9.6, 5); r3.AddPoint(10.6, 5); r3.AddPoint(10.6, 6); r3.AddPoint(9.6, 6); r3.AddPoint(9.6, 5)
        g3.AddGeometry(r3)
        p3.SetGeometry(g3)
        p3.SetField('event_id', 100)
        p3.SetField('event_layer_id', 30)
        poly_layer.CreateFeature(p3)

        self.ds = ds

        # Setup Layers Table
        conn = sqlite3.connect(self.gpkg_path)
        c = conn.cursor()
        c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (30, 'POOLS', 'Polygon')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.ds = None
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_count_partial_sum(self):
        """Test counting pools with partial overlap without intermediate rounding."""
        metrics_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'POOLS',
                    'usage': 'numerator' 
                }
            ]
        }
        
        # Expected:
        # P1: 1.0
        # P2: 0.5 (approx, due to projection it might vary slightly but basically .5)
        # P3: 0.4
        # Total: 1.9
        
        # If code rounds each:
        # P1: 1
        # P2: round(0.5) -> 0
        # P3: round(0.4) -> 0
        # Total: 1
        
        result = count(
            self.gpkg_path,
            sample_frame_feature_id=1,
            event_id=100,
            metric_params=metrics_params,
            analysis_params={}
        )
        
        # We assert that we get close to 1.9, establishing that we want floating point precision summing
        self.assertAlmostEqual(result, 1.9, delta=0.1)

if __name__ == '__main__':
    unittest.main()
