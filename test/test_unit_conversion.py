import os
import sys
import unittest

from qgis.core import QgsUnitTypes

from .utilities import get_qgis_app

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..src.lib.unit_conversion import RatioUnit, distance_units, short_unit_name

# Initialize QGIS app
get_qgis_app()


class TestUnitConversion(unittest.TestCase):
    def test_short_unit_name_distance(self):
        """Test short_unit_name for distance units."""
        # We rely on QGIS behavior here, so we test a few known ones
        # Meters
        unit_str = QgsUnitTypes.toString(QgsUnitTypes.DistanceMeters)
        abbr = short_unit_name(unit_str)
        # Typically 'm' or 'meters' depending on QGIS locale/version, but 'm' is standard
        self.assertTrue(abbr in ["m", "meters"], f"Expected abbreviation for meters, got {abbr}")

        # Feet
        unit_str = QgsUnitTypes.toString(QgsUnitTypes.DistanceFeet)
        abbr = short_unit_name(unit_str)
        self.assertTrue(abbr in ["ft", "feet"], f"Expected abbreviation for feet, got {abbr}")

    def test_short_unit_name_special(self):
        """Test special cases in short_unit_name."""
        self.assertEqual(short_unit_name("ratio"), "ratio")
        self.assertEqual(short_unit_name("percent"), "%")
        self.assertEqual(short_unit_name("count"), "#")

    def test_ratio_unit(self):
        """Test RatioUnit subclass behavior."""
        # Test toString
        self.assertEqual(RatioUnit.toString(RatioUnit.Ratio), "ratio")

        # Test fromString
        self.assertEqual(RatioUnit.fromString("ratio"), RatioUnit.Ratio)

        # Test fromUnitToUnitFactor
        self.assertEqual(RatioUnit.fromUnitToUnitFactor(RatioUnit.Ratio, RatioUnit.Ratio), 1)

        # Test fromUnitToUnit
        val = 15.5
        self.assertEqual(RatioUnit.fromUnitToUnit(val, RatioUnit.Ratio, RatioUnit.Ratio), val)

    def test_unknown_unit(self):
        """Test behavior for unknown unit."""
        self.assertEqual(short_unit_name("unknown_stuff"), "unknown_stuff")


if __name__ == "__main__":
    unittest.main()
