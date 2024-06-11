import os
import json
import requests
import webbrowser

from osgeo import ogr

from qgis.core import QgsGeometry

from typing import List

CLIMATE_ENGINE_API = 'https://api.climateengine.org'
CLIMATE_ENGINE_URL = 'https://www.climateengine.org/'
CLIMATE_ENGINE_MACHINE_CODE = 'Climate Engine'

def get_api_key():

    # Get the API key from environment variable
    api_key = os.getenv('CLIMATE_ENGINE_API_KEY')

    return api_key


def get_datasets() -> dict:
    datasets_file = os.path.join(os.path.dirname(__file__), 'climate_engine_datasets.json')
    with open(datasets_file, 'r') as f:
        datasets = json.load(f)
    return datasets


def get_dataset_variables(dataset: str) -> dict:
    api_key = get_api_key()
    if  api_key is None:
        return None
    url = f'{CLIMATE_ENGINE_API}/metadata/dataset_variables'
    headers = {'accept': 'application/json',    
               'Authorization': api_key}
    params = {'dataset': dataset}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        content = response.json()
        return {name: description for name, description in zip(content['variables'], content['variable names'])}
    else:
        return None
    

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
        return content
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

    url = f'{CLIMATE_ENGINE_API}/timeseries/native/polygons'
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

    url = f'{CLIMATE_ENGINE_API}/timeseries/native/polygons'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def open_climate_engine_website():

    webbrowser.open(CLIMATE_ENGINE_URL)
    