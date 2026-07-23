import json
import os
import webbrowser

from osgeo import ogr
from qgis.core import QgsGeometry
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox
import requests

from ..QRiS.settings import Settings

# Global timeout for all requests
API_TIMEOUT = 30

CLIMATE_ENGINE_API = "https://api.climateengine.org"  # DEBUG: 'https://api-dev.climateengine.org'
CLIMATE_ENGINE_URL = "https://www.climateengine.org/"
CLIMATE_ENGINE_MACHINE_CODE = "Climate Engine"
CLIMATE_ENGINE_CREDENTIAL_SETTING = "CLIMATE_ENGINE_AUTH_TOKEN"


def get_api_key():

    # Get the API key from environment variable
    api_key = None

    # If not found in environment, get it from QGIS settings.
    if api_key is None:
        api_key = Settings().getSecureValue(CLIMATE_ENGINE_CREDENTIAL_SETTING)

    return api_key


def clear_api_key() -> None:
    Settings().setSecureValue(CLIMATE_ENGINE_CREDENTIAL_SETTING, None)


def require_api_key(parent=None, open_settings_callback=None) -> bool:
    """Show a warning and return False if no API key is configured."""
    if get_api_key():
        return True
    msg = QMessageBox(parent)
    msg.setWindowTitle("Climate Engine API Key Required")
    msg.setTextFormat(Qt.PlainText)
    msg.setText("A Climate Engine API key has not been configured.\n\nPlease set your Climate Engine API key in the QRiS Settings")
    msg.setIcon(QMessageBox.Information)
    if open_settings_callback:
        btn_settings = msg.addButton("Open Settings", QMessageBox.ActionRole)
    msg.addButton(QMessageBox.Cancel)
    msg.exec_()
    if open_settings_callback and msg.clickedButton() == btn_settings:
        open_settings_callback()
    return False


def check_climate_engine_api_key(api_key: str) -> bool:
    url = f"{CLIMATE_ENGINE_API}/home/validate_key"
    headers = {"accept": "application/json", "Authorization": api_key}
    response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
    return response.status_code == 200


def get_datasets() -> dict:
    datasets_json_path = Settings().getValue("climateEngineJson")
    if datasets_json_path and os.path.exists(datasets_json_path):
        with open(datasets_json_path) as f:
            datasets = json.load(f)
        return {dataset["datasetId"]: dataset for dataset in datasets}
    else:
        return {}


def get_dataset_date_range(dataset: str) -> dict:
    api_key = get_api_key()
    if api_key is None:
        return None
    url = f"{CLIMATE_ENGINE_API}/metadata/dataset_dates"
    headers = {"accept": "application/json", "Authorization": api_key}

    params = {"dataset": dataset}
    response = requests.get(url, params=params, headers=headers, timeout=API_TIMEOUT)

    if response.status_code == 200:
        content = response.json()
        return content.get("Data", None)
    else:
        return None


def get_dataset_timeseries_polygon(dataset: str, variables: list[str], start_date: str, end_date: str, geometry: ogr.Geometry, area_reducer: str = "mean") -> dict:
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

    params = {"dataset": dataset, "variable": ",".join(variables), "area_reducer": area_reducer, "start_date": start_date, "end_date": end_date, "coordinates": f"[{json.dumps(coordinates)}]"}

    url = f"{CLIMATE_ENGINE_API}/timeseries/native/coordinates"
    headers = {"accept": "application/json", "Authorization": api_key}
    response = requests.post(url, data=params, headers=headers, timeout=API_TIMEOUT)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_dataset_zonal_stats_polygon(dataset: str, variables: list[str], start_date: str, end_date: str, geometry: ogr.Geometry, area_reducer: str = "mean", temporal_statistic: str = "mean") -> dict:
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

    params = {"dataset": dataset, "variable": variables, "temporal_statistic": temporal_statistic, "area_reducer": area_reducer, "start_date": start_date, "end_date": end_date, "coordinates": f"[{coordinates}]"}

    url = f"{CLIMATE_ENGINE_API}/timeseries/native/coordinates"
    headers = {"accept": "application/json", "Authorization": api_key}
    response = requests.post(url, data=params, headers=headers, timeout=API_TIMEOUT)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_raster_mapid(dataset: str, variable: str, temporal_statistic: str, start_date: str, end_date: str, color_map_opacity: float = 1.0) -> str:
    api_key = get_api_key()
    if api_key is None:
        return None
    headers = {"accept": "application/json", "Authorization": api_key}

    # Set up parameters dictionary for API call
    params_1 = {"dataset": dataset, "variable": variable, "temporal_statistic": temporal_statistic, "start_date": start_date, "end_date": end_date, "colormap_opacity": color_map_opacity}

    # Send API request
    url = f"{CLIMATE_ENGINE_API}/raster/mapid/values"
    r = requests.get(url, params=params_1, headers=headers, timeout=API_TIMEOUT)
    r.raise_for_status()
    if r.status_code != 200:
        return None
    response_content = r.json()
    data = response_content.get("Data", None)
    if data is None:
        return None
    map_tile_url = data.get("tile_fetcher", None)

    return map_tile_url


def open_climate_engine_website(path: str = ""):

    url = CLIMATE_ENGINE_URL + path

    webbrowser.open(url)
