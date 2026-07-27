"""Tests for analysis_metrics filtering logic."""

import json
import unittest

from osgeo import gdal, ogr

from ..src.gp.analysis_metrics import MetricCalculationError, get_metric_layer_features
from .metric_test_fixtures import cleanup_temp_gpkg, create_dce_layer, create_layers_table, create_spatial_ref, create_temp_gpkg

# Use standard test utility to start QGIS
from .utilities import get_qgis_app

get_qgis_app()

gdal.UseExceptions()


class TestMetricFiltering(unittest.TestCase):
    def setUp(self):
        self.test_dir, self.gpkg_path, self.ds = create_temp_gpkg()

        # Create Data Layer
        srs = create_spatial_ref(26912)
        layer = create_dce_layer(self.ds, "dce_points", srs, ogr.wkbPoint25D)

        self.layer = layer

        # Setup SQL tables
        create_layers_table(self.gpkg_path, [(1, "BEAVER_DAMS", "Point")])

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

        self.metric_layer_def = {"layer_id_ref": "BEAVER_DAMS", "attribute_filter": {"field_id_ref": "type", "values": ["dam"]}}

    def tearDown(self):
        self.ds = cleanup_temp_gpkg(self.ds, self.test_dir)

    def test_missing_attribute_error(self):
        """Test that missing attribute raises MetricCalculationError."""
        layer = self.layer
        # Add feature with missing field
        feat = ogr.Feature(layer.GetLayerDefn())
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(500000, 4500000)
        feat.SetGeometry(geom)
        feat.SetField("event_id", 100)
        feat.SetField("event_layer_id", 1)
        # MISSING 'type'
        feat.SetField("metadata", json.dumps({"attributes": {"other": "val"}}))
        layer.CreateFeature(feat)

        gen = get_metric_layer_features(self.gpkg_path, self.metric_layer_def, 100, self.sf_geom, {})

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
        feat.SetField("event_id", 100)
        feat.SetField("event_layer_id", 1)
        # NULL 'type'
        feat.SetField("metadata", json.dumps({"attributes": {"type": None}}))
        layer.CreateFeature(feat)

        gen = get_metric_layer_features(self.gpkg_path, self.metric_layer_def, 100, self.sf_geom, {})

        with self.assertRaises(MetricCalculationError) as cm:
            next(gen)
        self.assertIn("has a NULL value", str(cm.exception))


if __name__ == "__main__":
    unittest.main()



