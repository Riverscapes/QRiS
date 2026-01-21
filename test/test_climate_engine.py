
import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock, mock_open

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utilities import get_qgis_app
get_qgis_app()

from qgis.core import QgsGeometry, QgsPointXY, QgsPolygon
from qris_dev.src.lib import climate_engine

class TestClimateEngine(unittest.TestCase):

    @patch('os.getenv')
    def test_get_api_key(self, mock_getenv):
        mock_getenv.return_value = 'fake_key'
        self.assertEqual(climate_engine.get_api_key(), 'fake_key')
        mock_getenv.assert_called_with('CLIMATE_ENGINE_API_KEY')

    @patch('builtins.open', new_callable=mock_open, read_data='[{"datasetId": "test_id", "name": "Test Dataset"}]')
    def test_get_datasets(self, mock_file):
        # We mock the file opening to avoid reading the actual file system
        datasets = climate_engine.get_datasets()
        self.assertIn("test_id", datasets)
        self.assertEqual(datasets["test_id"]["name"], "Test Dataset")

    @patch('qris_dev.src.lib.climate_engine.get_api_key')
    @patch('requests.get')
    def test_get_dataset_date_range_success(self, mock_get, mock_get_api_key):
        mock_get_api_key.return_value = 'fake_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Data': {'start': '2000-01-01', 'end': '2020-12-31'}}
        mock_get.return_value = mock_response

        result = climate_engine.get_dataset_date_range('test_dataset')
        
        self.assertEqual(result, {'start': '2000-01-01', 'end': '2020-12-31'})
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('metadata/dataset_dates', args[0])
        self.assertEqual(kwargs['headers']['Authorization'], 'fake_key')

    @patch('qris_dev.src.lib.climate_engine.get_api_key')
    def test_get_dataset_date_range_no_key(self, mock_get_api_key):
        mock_get_api_key.return_value = None
        result = climate_engine.get_dataset_date_range('test_dataset')
        self.assertIsNone(result)

    @patch('qris_dev.src.lib.climate_engine.get_api_key')
    @patch('requests.get')
    def test_get_dataset_timeseries_polygon_qgsgeometry(self, mock_get, mock_get_api_key):
        mock_get_api_key.return_value = 'fake_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'date': '2020-01-01', 'value': 10}]
        mock_get.return_value = mock_response

        # Create a simple QgsGeometry (Polygon)
        # Polygon from 0,0 to 10,0 to 10,10 to 0,10 to 0,0
        wkt = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
        geometry = QgsGeometry.fromWkt(wkt)
        
        result = climate_engine.get_dataset_timeseries_polygon(
            dataset='test_ds', 
            variables=['var1'], 
            start_date='2020-01-01', 
            end_date='2020-01-31', 
            geometry=geometry
        )
        
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        # Check if coordinates key is in params
        self.assertIn('coordinates', kwargs['params'])
        # Check structure of coordinates string. logic is f'[{coordinates}]' where coordinates is list of [x, y]
        # It should look something like "[[0.0, 0.0], [10.0, 0.0], ...]"
        self.assertIn("[0.0, 0.0]", kwargs['params']['coordinates'])

    @patch('qris_dev.src.lib.climate_engine.get_api_key')
    @patch('requests.get')
    def test_get_dataset_zonal_stats_polygon(self, mock_get, mock_get_api_key):
        mock_get_api_key.return_value = 'fake_key'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'mean': 5.5}
        mock_get.return_value = mock_response

        wkt = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
        geometry = QgsGeometry.fromWkt(wkt)

        result = climate_engine.get_dataset_zonal_stats_polygon(
            dataset='test_ds',
            variables=['var1'],
            start_date='2020-01-01',
            end_date='2020-01-31',
            geometry=geometry
        )

        self.assertEqual(result, {'mean': 5.5})
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['area_reducer'], 'mean')
        self.assertEqual(kwargs['params']['temporal_statistic'], 'mean')

if __name__ == "__main__":
    unittest.main()
