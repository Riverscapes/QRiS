"""Tests for analysis_metrics count calculation."""

import unittest

from osgeo import gdal, ogr

from ..src.gp.analysis_metrics import count
from .metric_test_fixtures import cleanup_temp_gpkg, create_dce_layer, create_layers_table, create_sample_frame_layer, create_spatial_ref, create_temp_gpkg

# Use standard test utility to start QGIS
from .utilities import get_qgis_app

get_qgis_app()

gdal.UseExceptions()


class TestMetricCount(unittest.TestCase):
    def setUp(self):
        self.test_dir, self.gpkg_path, self.ds = create_temp_gpkg()

        # WGS84 Spatial Ref (Project Standard)
        srs = create_spatial_ref(4326)

        # 1. Create Sample Frame Layer (1x1 degree box for simplicity)
        create_sample_frame_layer(
            self.ds,
            srs,
            ring_points=[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
            fid=1,
        )

        # 2. Create Pools Layer (Polygons)
        # ID 30
        poly_layer = create_dce_layer(self.ds, "dce_polygons", srs, ogr.wkbPolygon25D)

        # Pool 1: Fully Inside (Area 1)
        # 1,1 to 2,2
        p1 = ogr.Feature(poly_layer.GetLayerDefn())
        g1 = ogr.Geometry(ogr.wkbPolygon)
        r1 = ogr.Geometry(ogr.wkbLinearRing)
        r1.AddPoint(1, 1)
        r1.AddPoint(2, 1)
        r1.AddPoint(2, 2)
        r1.AddPoint(1, 2)
        r1.AddPoint(1, 1)
        g1.AddGeometry(r1)
        p1.SetGeometry(g1)
        p1.SetField("event_id", 100)
        p1.SetField("event_layer_id", 30)
        poly_layer.CreateFeature(p1)

        # Pool 2: 50% Inside (Area 1, 0.5 inside)
        # Center on edge x=10. 9.5 to 10.5
        p2 = ogr.Feature(poly_layer.GetLayerDefn())
        g2 = ogr.Geometry(ogr.wkbPolygon)
        r2 = ogr.Geometry(ogr.wkbLinearRing)
        r2.AddPoint(9.5, 1)
        r2.AddPoint(10.5, 1)
        r2.AddPoint(10.5, 2)
        r2.AddPoint(9.5, 2)
        r2.AddPoint(9.5, 1)
        g2.AddGeometry(r2)
        p2.SetGeometry(g2)
        p2.SetField("event_id", 100)
        p2.SetField("event_layer_id", 30)
        poly_layer.CreateFeature(p2)

        # Pool 3: 40% Inside (Area 1, 0.4 inside)
        # Center on edge x=10. 9.6 to 10.6
        p3 = ogr.Feature(poly_layer.GetLayerDefn())
        g3 = ogr.Geometry(ogr.wkbPolygon)
        r3 = ogr.Geometry(ogr.wkbLinearRing)
        r3.AddPoint(9.6, 5)
        r3.AddPoint(10.6, 5)
        r3.AddPoint(10.6, 6)
        r3.AddPoint(9.6, 6)
        r3.AddPoint(9.6, 5)
        g3.AddGeometry(r3)
        p3.SetGeometry(g3)
        p3.SetField("event_id", 100)
        p3.SetField("event_layer_id", 30)
        poly_layer.CreateFeature(p3)

        # Setup Layers Table
        create_layers_table(self.gpkg_path, [(30, "POOLS", "Polygon")])

    def tearDown(self):
        self.ds = cleanup_temp_gpkg(self.ds, self.test_dir)

    def test_count_partial_sum(self):
        """Test counting pools with partial overlap without intermediate rounding."""
        metrics_params = {"dce_layers": [{"layer_id_ref": "POOLS", "usage": "numerator"}]}

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

        result = count(self.gpkg_path, sample_frame_feature_id=1, event_id=100, metric_params=metrics_params, analysis_params={})

        # We assert that we get close to 1.9, establishing that we want floating point precision summing
        self.assertAlmostEqual(result, 1.9, delta=0.1)


if __name__ == "__main__":
    unittest.main()



