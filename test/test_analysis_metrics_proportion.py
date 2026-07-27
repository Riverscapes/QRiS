"""Tests for analysis_metrics proportion calculation."""

import json
import unittest

from osgeo import gdal, ogr

from ..src.gp.analysis_metrics import proportion
from .metric_test_fixtures import cleanup_temp_gpkg, create_dce_layer, create_layers_table, create_sample_frame_layer, create_spatial_ref, create_temp_gpkg

# Use standard test utility to start QGIS
from .utilities import get_qgis_app

get_qgis_app()


gdal.UseExceptions()


class TestMetricProportion(unittest.TestCase):
    def setUp(self):
        self.test_dir, self.gpkg_path, self.ds = create_temp_gpkg()

        # WGS84 Spatial Ref (Project Standard)
        srs = create_spatial_ref(4326)

        # 1. Create Sample Frame Layer
        # Create a Sample Frame Feature (Approx 1 degree box for simplicity of checking intersection, though huge)
        # Centered at -111.0, 42.0 (Utah ish)
        create_sample_frame_layer(
            self.ds,
            srs,
            ring_points=[
                (-111.005, 42.000),
                (-110.995, 42.000),
                (-110.995, 42.010),
                (-111.005, 42.010),
                (-111.005, 42.000),
            ],
            fid=1,
        )

        # 2. Create Denominator Layer (Lines) - e.g. "Main Channel"
        # Renamed to dce_lines to match Layer.DCE_LAYER_NAMES default
        lines_layer = create_dce_layer(self.ds, "dce_lines", srs, ogr.wkbLineString25D)

        # Add a line that spans full width of SF
        line_feat = ogr.Feature(lines_layer.GetLayerDefn())
        line_geom = ogr.Geometry(ogr.wkbLineString)
        line_geom.AddPoint(-111.005, 42.005)  # Left edge
        line_geom.AddPoint(-110.995, 42.005)  # Right edge
        line_feat.SetGeometry(line_geom)
        line_feat.SetField("event_id", 100)
        line_feat.SetField("event_layer_id", 10)  # ID 10
        lines_layer.CreateFeature(line_feat)

        # 3. Create Numerator Layer (Lines) - e.g. "Riffles" (Subset of main channel)
        # Half the length
        line_feat2 = ogr.Feature(lines_layer.GetLayerDefn())
        line_geom2 = ogr.Geometry(ogr.wkbLineString)
        line_geom2.AddPoint(-111.005, 42.005)  # Left edge
        line_geom2.AddPoint(-111.000, 42.005)  # Middle
        line_feat2.SetGeometry(line_geom2)
        line_feat2.SetField("event_id", 100)
        line_feat2.SetField("event_layer_id", 20)  # ID 20
        lines_layer.CreateFeature(line_feat2)

        # 4. Create Polygon Layer
        # Renamed to dce_polygons to match Layer.DCE_LAYER_NAMES default
        poly_layer = create_dce_layer(self.ds, "dce_polygons", srs, ogr.wkbPolygon25D)

        # A Polygon filling half the SF height
        poly_feat = ogr.Feature(poly_layer.GetLayerDefn())
        p_geom = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(-111.005, 42.000)
        ring.AddPoint(-110.995, 42.000)
        ring.AddPoint(-110.995, 42.005)  # Half height
        ring.AddPoint(-111.005, 42.005)
        ring.AddPoint(-111.005, 42.000)
        p_geom.AddGeometry(ring)
        poly_feat.SetGeometry(p_geom)
        poly_feat.SetField("event_id", 100)
        poly_feat.SetField("event_layer_id", 30)  # ID 30
        poly_layer.CreateFeature(poly_feat)

        # Setup Layers Table in SQLite
        # Note: geom_type matches keys in Layer.DCE_LAYER_NAMES
        create_layers_table(
            self.gpkg_path,
            [
                (10, "DENOM_LINES", "Linestring"),
                (20, "NUM_LINES", "Linestring"),
                (30, "NUM_POLYS", "Polygon"),
            ],
        )

    def tearDown(self):
        self.ds = cleanup_temp_gpkg(self.ds, self.test_dir)

    def test_line_length_proportion(self):
        """Test calculating proportion of length (Line within Line)."""
        metrics_params = {"dce_layers": [{"layer_id_ref": "DENOM_LINES", "usage": "denominator"}, {"layer_id_ref": "NUM_LINES", "usage": "numerator"}]}

        result = proportion(self.gpkg_path, sample_frame_feature_id=1, event_id=100, metric_params=metrics_params, analysis_params={})

        # Num is half of Denom
        self.assertAlmostEqual(result, 0.5, places=2)

    def test_polygon_area_proportion_of_sample_frame(self):
        """Test calculating proportion of area vs Sample Frame (Denominator Default)."""
        metrics_params = {
            "dce_layers": [
                {
                    "layer_id_ref": "NUM_POLYS",
                    "usage": "numerator",  # or just implicit input
                }
            ]
        }

        result = proportion(self.gpkg_path, sample_frame_feature_id=1, event_id=100, metric_params=metrics_params, analysis_params={})

        # Polygon covers bottom half of SF
        self.assertAlmostEqual(result, 0.5, places=2)

    def test_denominator_case_sensitivity_and_missing_usage(self):
        """Test denominator usage is case-insensitive and safe against missing keys."""
        metrics_params = {
            "dce_layers": [
                {
                    "layer_id_ref": "DENOM_LINES",
                    "usage": "Denominator",  # Mixed case
                },
                {"layer_id_ref": "NUM_LINES", "usage": "numerator"},
                {
                    "layer_id_ref": "SOME_IGNORED_LAYER"
                    # Missing usage key - should be ignored and not crash
                },
            ]
        }

        result = proportion(self.gpkg_path, sample_frame_feature_id=1, event_id=100, metric_params=metrics_params, analysis_params={})

        # Num is half of Denom
        self.assertAlmostEqual(result, 0.5, places=2)


if __name__ == "__main__":
    unittest.main()



