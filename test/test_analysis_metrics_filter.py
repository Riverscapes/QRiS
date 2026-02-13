"""Tests for analysis_metrics filtering logic."""
import unittest
import os
import shutil
import tempfile
import json
import sqlite3
import sys
# from unittest.mock import MagicMock

# Use standard test utility to start QGIS
try:
    from utilities import get_qgis_app
except ImportError:
    from .utilities import get_qgis_app

get_qgis_app()

from osgeo import ogr, osr, gdal
gdal.UseExceptions()

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__)) 
plugin_root = os.path.dirname(current_dir) 
parent_root = os.path.dirname(plugin_root) 

if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

from qris_dev.src.gp.analysis_metrics import get_metric_layer_features, MetricCalculationError

class TestMetricFiltering(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.gpkg_path = os.path.join(self.test_dir, 'test_project.gpkg')
        
        # Create GPKG
        driver = ogr.GetDriverByName('GPKG')
        ds = driver.CreateDataSource(self.gpkg_path)
        
        # Create Data Layer
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(26912) 
        layer = ds.CreateLayer('dce_points', srs=srs, geom_type=ogr.wkbPoint25D)
        layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))
        layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        
        self.ds = ds
        self.layer = layer

        # Setup SQL tables
        conn = sqlite3.connect(self.gpkg_path)
        c = conn.cursor()
        c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (1, 'BEAVER_DAMS', 'Point')")
        conn.commit()
        conn.close()

        # Dummy Sample Frame Geom
        self.sf_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(499000, 4499000)
        ring.AddPoint(501000, 4499000)
        ring.AddPoint(501000, 4501000)
        ring.AddPoint(499000, 4501000)
        ring.AddPoint(499000, 4499000)
        self.sf_geom.AddGeometry(ring)
        self.sf_geom.AssignSpatialReference(srs)
        
        self.metric_layer_def = {
            'layer_id_ref': 'BEAVER_DAMS',
            'attribute_filter': {
                'field_id_ref': 'type',
                'values': ['dam']
            }
        }

    def tearDown(self):
        self.ds = None
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass
            
    def test_missing_attribute_error(self):
        """Test that missing attribute raises MetricCalculationError."""
        layer = self.layer
        # Add feature with missing field
        feat = ogr.Feature(layer.GetLayerDefn())
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(500000, 4500000)
        feat.SetGeometry(geom)
        feat.SetField('event_id', 100)
        feat.SetField('event_layer_id', 1)
        # MISSING 'type'
        feat.SetField('metadata', json.dumps({'attributes': {'other': 'val'}}))
        layer.CreateFeature(feat)
        
        gen = get_metric_layer_features(
            self.gpkg_path, self.metric_layer_def, 100, self.sf_geom, {}
        )
        
        with self.assertRaises(MetricCalculationError) as cm:
            next(gen)
        self.assertIn("missing required attribute", str(cm.exception))

    def test_null_attribute_error(self):
        """Test that NULL attribute raises MetricCalculationError."""
        layer = self.layer
        # Add feature with NULL field
        feat = ogr.Feature(layer.GetLayerDefn())
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(500000, 4500000)
        feat.SetGeometry(geom)
        feat.SetField('event_id', 100)
        feat.SetField('event_layer_id', 1)
        # NULL 'type'
        feat.SetField('metadata', json.dumps({'attributes': {'type': None}}))
        layer.CreateFeature(feat)
        
        gen = get_metric_layer_features(
            self.gpkg_path, self.metric_layer_def, 100, self.sf_geom, {}
        )
        
        with self.assertRaises(MetricCalculationError) as cm:
            next(gen)
        self.assertIn("has a NULL value", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
