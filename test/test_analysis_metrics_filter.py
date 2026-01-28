"""Tests for analysis_metrics filtering logic."""
import unittest
import os
import shutil
import tempfile
import json
import sqlite3
from osgeo import ogr, osr

# Add src to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from qris_dev.src.gp.analysis_metrics import get_metric_layer_features, MetricCalculationError

class TestMetricFiltering(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.gpkg_path = os.path.join(self.test_dir, 'test_project.gpkg')
        
        # Create GPKG
        driver = ogr.GetDriverByName('GPKG')
        ds = driver.CreateDataSource(self.gpkg_path)
        
        # Create Data Layer (e.g. 'beaver_dams') - Name must match what get_dce_layer_source returns
        # We'll rely on our mock SQL to ensure get_dce_layer_source returns 'BEAVER_DAMS'
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(26912) 
        layer = ds.CreateLayer('dce_points', srs=srs, geom_type=ogr.wkbPoint)
        
        # Add Fields
        layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))
        layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        
        self.features = []

        # Helper
        def add_feat(attr_dict, evid=100, elid=1):
            feat = ogr.Feature(layer.GetLayerDefn())
            geom = ogr.Geometry(ogr.wkbPoint)
            geom.AddPoint(500000, 4500000)
            feat.SetGeometry(geom)
            feat.SetField('event_id', evid)
            feat.SetField('event_layer_id', elid)
            if attr_dict is not None:
                feat.SetField('metadata', json.dumps({'attributes': attr_dict}))
            layer.CreateFeature(feat)
            self.features.append(feat.GetFID())
            
        # FID 1: Valid Match
        add_feat({'type': 'dam'}) 
        # FID 2: Invalid Value
        add_feat({'type': 'lodge'}) 
        # FID 3: Missing Field
        add_feat({'other': 'val'}) 
        # FID 4: Null Value
        add_feat({'type': None}) 
        
        ds = None # Close
        
        # Setup SQL tables for QRIS lookups
        conn = sqlite3.connect(self.gpkg_path)
        c = conn.cursor()
        c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
        # id=1 matches elid=1
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (1, 'BEAVER_DAMS', 'Point')")
        conn.commit()
        conn.close()

        # Create Dummy Sample Frame Geom
        self.sf_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(499000, 4499000)
        ring.AddPoint(501000, 4499000)
        ring.AddPoint(501000, 4501000)
        ring.AddPoint(499000, 4501000)
        ring.AddPoint(499000, 4499000)
        self.sf_geom.AddGeometry(ring)
        self.sf_geom.AssignSpatialReference(srs)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_filtering_strictness(self):
        """Verify strict filtering for NULL or missing attributes."""
        
        metric_layer_def = {
            'layer_id_ref': 'BEAVER_DAMS',
            'attribute_filter': {
                'field_id_ref': 'type',
                'values': ['dam']
            }
        }
        
        # We need a small hack: get_dce_layer_source logic in analysis_metrics might be tricky to mock perfectly 
        # if it expects exact return format.
        # But let's assume get_dce_layer_source returns (id, fc_name).
        
        # Generator
        gen = get_metric_layer_features(
            self.gpkg_path,
            metric_layer_def,
            event_id=100,
            sample_frame_geom=self.sf_geom,
            analysis_params={}
        )
        
        # The generator processes feature by feature.
        # The order depends on OGR iteration (usually FID order).
        
        # Feature 1 (FID 1) -> Should match
        try:
            f1 = next(gen)
            self.assertEqual(f1.GetField('event_id'), 100)
        except StopIteration:
            self.fail("Feature 1 should have matched")
            
        # Feature 2 (FID 2) -> Should be skipped (value mismatch)
        # Feature 3 (FID 3) -> Missing 'type' -> Should RAISE Error
        
        with self.assertRaises(MetricCalculationError) as cm:
            next(gen)
        self.assertIn("missing required attribute", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
