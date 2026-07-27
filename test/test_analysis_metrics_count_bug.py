"""Tests for analysis_metrics count calculation bugs."""

import unittest

from osgeo import gdal, ogr

from ..src.gp.analysis_metrics import count
from .metric_test_fixtures import cleanup_temp_gpkg, create_dce_layer, create_layers_table, create_sample_frame_layer, create_spatial_ref, create_temp_gpkg

# Use standard test utility to start QGIS
from .utilities import get_qgis_app

get_qgis_app()

gdal.UseExceptions()


class TestMetricCountBug(unittest.TestCase):
    def setUp(self):
        self.test_dir, self.gpkg_path, self.ds = create_temp_gpkg()

        # WGS84 Spatial Ref (Project Standard)
        srs = create_spatial_ref(4326)

        # 1. Create Sample Frame Layer
        create_sample_frame_layer(
            self.ds,
            srs,
            ring_points=[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
            fid=1,
        )

        # 2. Create Points Layer (Countable)
        pt_layer = create_dce_layer(self.ds, "dce_points", srs, ogr.wkbPoint25D)

        # DCE 100: 15 points
        for _i in range(15):
            f = ogr.Feature(pt_layer.GetLayerDefn())
            g = ogr.Geometry(ogr.wkbPoint)
            g.AddPoint(5, 5)  # Inside
            f.SetGeometry(g)
            f.SetField("event_id", 100)
            f.SetField("event_layer_id", 10)
            pt_layer.CreateFeature(f)

        # DCE 200: 0 points (or maybe 2 for control)
        for _i in range(2):
            f = ogr.Feature(pt_layer.GetLayerDefn())
            g = ogr.Geometry(ogr.wkbPoint)
            g.AddPoint(5, 5)  # Inside
            f.SetGeometry(g)
            f.SetField("event_id", 200)
            f.SetField("event_layer_id", 10)
            pt_layer.CreateFeature(f)

        # Setup Layers Table
        create_layers_table(self.gpkg_path, [(10, "POINTS", "Point")])

    def tearDown(self):
        self.ds = cleanup_temp_gpkg(self.ds, self.test_dir)

    def test_count_respects_event_id(self):
        """Test count uses correct event_id."""
        metrics_params = {"dce_layers": [{"layer_id_ref": "POINTS", "usage": "numerator"}]}

        # Check DCE 100 -> 15
        val_100 = count(self.gpkg_path, 1, 100, metrics_params, {})
        self.assertEqual(val_100, 15)

        # Check DCE 200 -> 2
        val_200 = count(self.gpkg_path, 1, 200, metrics_params, {})
        self.assertEqual(val_200, 2)

    def test_count_excludes_normalization(self):
        """Test count logic excludes layers marked as usage=normalization."""
        metrics_params = {
            "dce_layers": [
                {"layer_id_ref": "POINTS", "usage": "numerator"},
                {"layer_id_ref": "POINTS", "usage": "normalization"},  # Same layer reused as fake normalization
            ]
        }

        # If it counts normalization layer, it will double count or add to it.
        # DCE 200 has 2 points.
        # If normalization is skipped in counting, we get 2. (Then divided by normalization factor, but here normalization factor calculation depends on 'input_ref' which is missing, so loop over norms might fail if I don't set it up,
        # but the COUNT loop is what I care about first).

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


if __name__ == "__main__":
    unittest.main()



