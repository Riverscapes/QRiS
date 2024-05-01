import requests as re

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


def get_dataset_date_range(dataset: str) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    url = f'{CLIMATE_ENGINE_URL}/metadata/dataset_dates'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    
    params = {'dataset': dataset}
    response = re.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    

    
def get_dataset_timeseries_polygon(dataset: str, variable: str, start_date: str, end_date: str, geometry: ogr.Geometry) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    
    coordinates = []

    url = f'{CLIMATE_ENGINE_URL}/timeseries/native/polygons?dataset={dataset}&'
    headers = {'accept': 'application/json',
               'Authorization': api_key}
    response = re.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None