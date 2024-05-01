import os
import json
import requests

from osgeo import ogr

from PyQt5.QtCore import QSettings

CLIMATE_ENGINE_URL = 'https://api.climateengine.org'

def get_api_key():
    from ..qris_toolbar import ORGANIZATION, APPNAME
    
    settings = QSettings(ORGANIZATION, APPNAME)
    api_key = None
    try:
        api_key = settings.value('climate_engine_api_key')
    except KeyError as e:
        print(e)
        api_key = None
    return api_key


def get_datasets() -> dict:
    datasets_file = os.path.join(os.path.dirname(__file__), 'climate_engine_datasets.json')
    with open(datasets_file, 'r') as f:
        datasets = json.load(f)
    return datasets


def get_dataset_variables(dataset: str) -> list:
    api_key = get_api_key()
    if  api_key is None:
        return None
    url = f'{CLIMATE_ENGINE_URL}/metadata/dataset_variables'
    headers = {'accept': 'application/json',    
               'Authorization': api_key}
    params = {'dataset': dataset}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        content = response.json()
        return content['variables']
    else:
        return None
    

def get_dataset_date_range(dataset: str) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    url = f'{CLIMATE_ENGINE_URL}/metadata/dataset_dates'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    
    params = {'dataset': dataset}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        content = response.json()
        return content
    else:
        return None
    

def get_dataset_timeseries_polygon(dataset: str, variable: str, start_date: str, end_date: str, geometry: ogr.Geometry) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    
    coordinates = []
    for i in range(geometry.GetPointCount()):
        pt = geometry.GetPoint(i)
        coordinates.append([pt[0], pt[1]])

    params = {'dataset': dataset,
              'variable': variable,
              'area_reducer': 'mean',
              'start_date': start_date,
              'end_date': end_date,
              'coordinates': f'[{coordinates}]'}

    url = f'{CLIMATE_ENGINE_URL}/timeseries/native/polygons'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None