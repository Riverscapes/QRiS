import unittest
from src.gp import stream_stats

class TestStreamStatsAPI(unittest.TestCase):
    def test_retrieve_flow_statistics_api(self):
        # Example coordinates for a valid USGS location (Utah)
        lat = 40.7608
        lon = -111.8910
        rcode = 'UT'
        # Delineate watershed
        watershed_data = stream_stats.delineate_watershed(lat, lon, rcode)
        self.assertIn('bcrequest', watershed_data)
        # Retrieve basin characteristics
        basin_chars = stream_stats.retrieve_basin_characteristics(watershed_data)
        self.assertIsInstance(basin_chars, dict)
        # Retrieve flow scenarios (calls regression regions, scenarios)
        flow_scenarios = stream_stats.retrieve_flow_scenarios(watershed_data, basin_chars)
        self.assertIsInstance(flow_scenarios, dict)
        self.assertIn('regressionRegions', flow_scenarios)
        self.assertIn('scenarios', flow_scenarios)
        
        # Calculate flow statistics
        flow_stats = stream_stats.calculate_flow_statistics(flow_scenarios, basin_chars)
        self.assertIsInstance(flow_stats, list)
        self.assertGreater(len(flow_stats), 0)

if __name__ == '__main__':
    unittest.main()
