"""Tests for analysis_metrics count calculation bugs."""
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

class TestMetricCountBug(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.gpkg_path = os.path.join(self.test_dir, 'test_project.gpkg')
        
        # Create GPKG
        driver = ogr.GetDriverByName('GPKG')
        ds = driver.CreateDataSource(self.gpkg_path)
        
        # WGS84 Spatial Ref (Project Standard)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326) 
        
        # 1. Create Sample Frame Layer
        sf_layer = ds.CreateLayer('sample_frame_features', srs=srs, geom_type=ogr.wkbPolygon)
        sf_layer.CreateField(ogr.FieldDefn('fid', ogr.OFTInteger))
        
        sf_feat = ogr.Feature(sf_layer.GetLayerDefn())
        sf_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(0, 0); ring.AddPoint(10, 0); ring.AddPoint(10, 10); ring.AddPoint(0, 10); ring.AddPoint(0, 0)
        sf_geom.AddGeometry(ring)
        sf_feat.SetGeometry(sf_geom)
        sf_feat.SetField('fid', 1)
        sf_layer.CreateFeature(sf_feat)
        
        # 2. Create Points Layer (Countable)
        pt_layer = ds.CreateLayer('dce_points', srs=srs, geom_type=ogr.wkbPoint)
        pt_layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        pt_layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        pt_layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))

        # DCE 100: 15 points
        for i in range(15):
            f = ogr.Feature(pt_layer.GetLayerDefn())
            g = ogr.Geometry(ogr.wkbPoint)
            g.AddPoint(5, 5) # Inside
            f.SetGeometry(g)
            f.SetField('event_id', 100)
            f.SetField('event_layer_id', 10)
            pt_layer.CreateFeature(f)

        # DCE 200: 0 points (or maybe 2 for control)
        for i in range(2):
            f = ogr.Feature(pt_layer.GetLayerDefn())
            g = ogr.Geometry(ogr.wkbPoint)
            g.AddPoint(5, 5) # Inside
            f.SetGeometry(g)
            f.SetField('event_id', 200)
            f.SetField('event_layer_id', 10)
            pt_layer.CreateFeature(f)
            
        self.ds = ds

        # Setup Layers Table
        conn = sqlite3.connect(self.gpkg_path)
        c = conn.cursor()
        c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (10, 'POINTS', 'Point')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.ds = None
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_count_respects_event_id(self):
        """Test count uses correct event_id."""
        metrics_params = {
            'dce_layers': [
                { 'layer_id_ref': 'POINTS', 'usage': 'numerator' }
            ]
        }
        
        # Check DCE 100 -> 15
        val_100 = count(self.gpkg_path, 1, 100, metrics_params, {})
        self.assertEqual(val_100, 15)
        
        # Check DCE 200 -> 2
        val_200 = count(self.gpkg_path, 1, 200, metrics_params, {})
        self.assertEqual(val_200, 2)

    def test_count_excludes_normalization(self):
        """Test count logic excludes layers marked as usage=normalization."""
        metrics_params = {
            'dce_layers': [
                { 'layer_id_ref': 'POINTS', 'usage': 'numerator' },
                { 'layer_id_ref': 'POINTS', 'usage': 'normalization' } # Same layer reused as fake normalization
            ]
        }
        
        # If it counts normalization layer, it will double count or add to it.
        # DCE 200 has 2 points.
        # If normalization is skipped in counting, we get 2. (Then divided by normalization factor, but here normalization factor calculation depends on 'input_ref' which is missing, so loop over norms might fail if I don't set it up, but the COUNT loop is what I care about first).
        
        # The count function calculates TOTAL count then divides.
        # If normalization layer is included in loop:
        # Loop 1 (Numerator): count += 2
        # Loop 2 (Normalization): count += 2
        # Total = 4
        # Then divide by normalization factor (if any).
        
        # Let's skip valid normalization setup for now to check the pure count issue.
        # Effectively, we just want to see if the loop processes it.
        
        val = count(self.gpkg_path, 1, 200, metrics_params, {})
        
        # If bug exists, it counts 4. If fixed, it counts 2.
        # Note: Since I didn't provide 'input_ref' in normalization layer, the normalization calc loop at the end of `count` function
        # checks `if layer_ref is not None:`. 'input_ref' is None here, so it won't divide.
        # So we see the raw sum.
        
        self.assertEqual(val, 2, "Should exclude normalization layer from count summation")

if __name__ == '__main__':
    unittest.main()
