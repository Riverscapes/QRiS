"""Tests for analysis_metrics proportion calculation."""
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

# Import after path setup and mocking
from qris_dev.src.gp.analysis_metrics import proportion

class TestMetricProportion(unittest.TestCase):

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
        sf_layer = ds.CreateLayer('sample_frame_features', srs=srs, geom_type=ogr.wkbPolygon25D)
        sf_layer.CreateField(ogr.FieldDefn('fid', ogr.OFTInteger))
        
        # Create a Sample Frame Feature (Approx 1 degree box for simplicity of checking intersection, though huge)
        # Centered at -111.0, 42.0 (Utah ish)
        sf_feat = ogr.Feature(sf_layer.GetLayerDefn())
        sf_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-111.005, 42.000)
        ring.AddPoint(-110.995, 42.000)
        ring.AddPoint(-110.995, 42.010)
        ring.AddPoint(-111.005, 42.010)
        ring.AddPoint(-111.005, 42.000)
        sf_geom.AddGeometry(ring)
        sf_feat.SetGeometry(sf_geom)
        sf_feat.SetField('fid', 1)
        sf_layer.CreateFeature(sf_feat)
        
        # 2. Create Denominator Layer (Lines) - e.g. "Main Channel"
        # Renamed to dce_lines to match Layer.DCE_LAYER_NAMES default
        lines_layer = ds.CreateLayer('dce_lines', srs=srs, geom_type=ogr.wkbLineString25D)
        lines_layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        lines_layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        lines_layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))
        
        # Add a line that spans full width of SF
        line_feat = ogr.Feature(lines_layer.GetLayerDefn())
        line_geom = ogr.Geometry(ogr.wkbLineString)
        line_geom.AddPoint(-111.005, 42.005) # Left edge
        line_geom.AddPoint(-110.995, 42.005) # Right edge
        line_feat.SetGeometry(line_geom)
        line_feat.SetField('event_id', 100)
        line_feat.SetField('event_layer_id', 10) # ID 10
        lines_layer.CreateFeature(line_feat)
        
        # 3. Create Numerator Layer (Lines) - e.g. "Riffles" (Subset of main channel)
        # Half the length
        line_feat2 = ogr.Feature(lines_layer.GetLayerDefn())
        line_geom2 = ogr.Geometry(ogr.wkbLineString)
        line_geom2.AddPoint(-111.005, 42.005) # Left edge
        line_geom2.AddPoint(-111.000, 42.005) # Middle
        line_feat2.SetGeometry(line_geom2)
        line_feat2.SetField('event_id', 100)
        line_feat2.SetField('event_layer_id', 20) # ID 20
        lines_layer.CreateFeature(line_feat2)

        # 4. Create Polygon Layer
        # Renamed to dce_polygons to match Layer.DCE_LAYER_NAMES default
        poly_layer = ds.CreateLayer('dce_polygons', srs=srs, geom_type=ogr.wkbPolygon25D)
        poly_layer.CreateField(ogr.FieldDefn('event_id', ogr.OFTInteger))
        poly_layer.CreateField(ogr.FieldDefn('event_layer_id', ogr.OFTInteger))
        poly_layer.CreateField(ogr.FieldDefn('metadata', ogr.OFTString))

        # A Polygon filling half the SF height
        poly_feat = ogr.Feature(poly_layer.GetLayerDefn())
        p_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-111.005, 42.000)
        ring.AddPoint(-110.995, 42.000)
        ring.AddPoint(-110.995, 42.005) # Half height
        ring.AddPoint(-111.005, 42.005)
        ring.AddPoint(-111.005, 42.000)
        p_geom.AddGeometry(ring)
        poly_feat.SetGeometry(p_geom)
        poly_feat.SetField('event_id', 100)
        poly_feat.SetField('event_layer_id', 30) # ID 30
        poly_layer.CreateFeature(poly_feat)
        
        self.ds = ds

        # Setup Layers Table in SQLite
        conn = sqlite3.connect(self.gpkg_path)
        c = conn.cursor()
        c.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
        # Note: geom_type matches keys in Layer.DCE_LAYER_NAMES
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (10, 'DENOM_LINES', 'Linestring')")
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (20, 'NUM_LINES', 'Linestring')")
        c.execute("INSERT INTO layers (id, fc_name, geom_type) VALUES (30, 'NUM_POLYS', 'Polygon')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.ds = None
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_line_length_proportion(self):
        """Test calculating proportion of length (Line within Line)."""
        metrics_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'DENOM_LINES',
                    'usage': 'denominator'
                },
                {
                    'layer_id_ref': 'NUM_LINES',
                    'usage': 'numerator'
                }
            ]
        }
        
        result = proportion(
            self.gpkg_path,
            sample_frame_feature_id=1,
            event_id=100,
            metric_params=metrics_params,
            analysis_params={}
        )
        
        # Num is half of Denom
        self.assertAlmostEqual(result, 0.5, places=2)

    def test_polygon_area_proportion_of_sample_frame(self):
        """Test calculating proportion of area vs Sample Frame (Denominator Default)."""
        metrics_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'NUM_POLYS',
                    'usage': 'numerator' # or just implicit input
                }
            ]
        }
        
        result = proportion(
            self.gpkg_path,
            sample_frame_feature_id=1,
            event_id=100,
            metric_params=metrics_params,
            analysis_params={}
        )
        
        # Polygon covers bottom half of SF
        self.assertAlmostEqual(result, 0.5, places=2)


    def test_denominator_case_sensitivity_and_missing_usage(self):
        """Test denominator usage is case-insensitive and safe against missing keys."""
        metrics_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'DENOM_LINES',
                    'usage': 'Denominator'  # Mixed case
                },
                {
                    'layer_id_ref': 'NUM_LINES',
                    'usage': 'numerator'
                },
                {
                    'layer_id_ref': 'SOME_IGNORED_LAYER'
                    # Missing usage key - should be ignored and not crash
                }
            ]
        }
        
        result = proportion(
            self.gpkg_path,
            sample_frame_feature_id=1,
            event_id=100,
            metric_params=metrics_params,
            analysis_params={}
        )
        
        # Num is half of Denom
        self.assertAlmostEqual(result, 0.5, places=2)

if __name__ == '__main__':
    unittest.main()
