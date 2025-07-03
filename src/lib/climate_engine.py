import os
import json
import requests
import webbrowser

from osgeo import ogr

from qgis.core import QgsGeometry

from typing import List

CLIMATE_ENGINE_API = 'https://api.climateengine.org' # DEBUG: 'https://api-dev.climateengine.org'
CLIMATE_ENGINE_URL = 'https://www.climateengine.org/'
CLIMATE_ENGINE_MACHINE_CODE = 'Climate Engine'

def get_api_key():

    # Get the API key from environment variable
    api_key = os.getenv('CLIMATE_ENGINE_API_KEY')

    return api_key


def get_datasets() -> dict:
    datasets_file = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'climate_engine_datasets.json')
    with open(datasets_file, 'r') as f:
        datasets = json.load(f)
    return {dataset['datasetId']: dataset for dataset in datasets}
    

def get_dataset_date_range(dataset: str) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    url = f'{CLIMATE_ENGINE_API}/metadata/dataset_dates'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    
    params = {'dataset': dataset}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        content = response.json()
        return content.get('Data', None)
    else:
        return None
    

def get_dataset_timeseries_polygon(dataset: str, variables: List[str], start_date: str, end_date: str, geometry: ogr.Geometry, area_reducer: str='mean') -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    
    if isinstance(variables, str):
        variables = [variables]

    coordinates = []
    if isinstance(geometry, QgsGeometry):
        for pt in geometry.asPolygon()[0]:
            coordinates.append([pt.x(), pt.y()])
    else:
        for i in range(geometry.GetPointCount()):
            pt = geometry.GetPoint(i)
            coordinates.append([pt[0], pt[1]])

    params = {'dataset': dataset,
              'variable': ','.join(variables),
              'area_reducer': area_reducer,
              'start_date': start_date,
              'end_date': end_date,
              'coordinates': f'[{coordinates}]'}

    url = f'{CLIMATE_ENGINE_API}/timeseries/native/coordinates'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    

def get_dataset_zonal_stats_polygon(dataset: str, variables: List[str], start_date: str, end_date: str, geometry: ogr.Geometry, area_reducer: str='mean', temporal_statistic: str='mean') -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    
    if isinstance(variables, str):
        variables = [variables]

    coordinates = []
    if isinstance(geometry, QgsGeometry):
        for pt in geometry.asPolygon()[0]:
            coordinates.append([pt.x(), pt.y()])
    else:
        for i in range(geometry.GetPointCount()):
            pt = geometry.GetPoint(i)
            coordinates.append([pt[0], pt[1]])

    params = {'dataset': dataset,
              'variable': variables,
              'temporal_statistic': temporal_statistic,
              'area_reducer': area_reducer,
              'start_date': start_date,
              'end_date': end_date,
              'coordinates': f'[{coordinates}]'}

    url = f'{CLIMATE_ENGINE_API}/timeseries/native/coordinates'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def get_raster_mapid(dataset: str, variable: str, temporal_statistic: str, start_date: str, end_date: str, color_map_opacity: float=1.0) -> str:
    api_key = get_api_key()
    if api_key is None:
        return None
    headers = {'accept': 'application/json',
            'Authorization': api_key}
    
    #Set up parameters dictionary for API call
    params_1 = {
        'dataset': dataset,
        'variable': variable,
        'temporal_statistic': temporal_statistic,
        'start_date': start_date,
        'end_date': end_date,
        'colormap_opacity': color_map_opacity
    }

    # Send API request
    url = f'{CLIMATE_ENGINE_API}/raster/mapid/values'
    r = requests.get(url, params=params_1, headers=headers, verify=False)
    r.raise_for_status()
    if r.status_code != 200:
        return None
    response_content = r.json()
    data = response_content.get('Data', None)
    if data is None:
        return None
    map_tile_url = data.get('tile_fetcher', None)

    return map_tile_url


def open_climate_engine_website():

    webbrowser.open(CLIMATE_ENGINE_URL)
    