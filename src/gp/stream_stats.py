from asyncio import streams
from termios import ECHOE
from urllib import response
import requests
import json
import os
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsTask, QgsMessageLog, Qgis
from ..model.pour_point import save_pour_point, PourPoint
from qgis.PyQt.QtCore import pyqtSignal

MESSAGE_CATEGORY = 'QRiS_StreamStatsTask'


class StreamStats(QgsTask):

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    stream_stats_successfully_complete = pyqtSignal(PourPoint, bool)

    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    def __init__(self, db_path: str, latitude: float, longitude: float, name: str, description: str, get_basic_chars: bool, get_flow_stats: bool, add_to_map: bool):
        super().__init__(f'{name} Stream Stats API Request at {longitude}, {latitude}', QgsTask.CanCancel)
        # self.duration = duration
        self.db_path = db_path
        self.name = name
        self.qris_description = description
        self.latitude = latitude
        self.longitude = longitude
        self.get_basin_chars = get_basic_chars
        self.get_flow_stats = get_flow_stats
        self.add_to_map = add_to_map
        self.pour_point = None
        self.total = 0
        self.iterations = 0
        self.exception = None

    def run(self):
        """Heavy lifting and periodically check for isCanceled() and gracefully abort.
        Must return True or False. Raising exceptions will crash QGIS"""

        QgsMessageLog.logMessage(f'Started {self.name} Stream Stats API Request ', MESSAGE_CATEGORY, Qgis.Info)

        try:
            state_code = get_state_from_coordinates(self.latitude, self.longitude)

            if state_code is None:
                self.exception = Exception('Failed to determine US State of the point. Ensure that the point within the United States.')
                return False

            if self.isCanceled():
                return False

            self.watershed_data = delineate_watershed(self.latitude, self.longitude, state_code)
            workspace_id = self.watershed_data['workspaceID'] if 'workspaceID' in self.watershed_data else None

            if self.isCanceled():
                return False

            basin_chars = None
            if self.get_basin_chars is True:
                if workspace_id is None:
                    self.exception = Exception('Unable to retrieve basin characteristics because no workspace ID was available from watershed delineation.')
                    return False

                basin_chars = retrieve_basin_characteristics(state_code, workspace_id)

            if self.isCanceled():
                return False

            flow_stats = None
            if self.get_flow_stats is True:
                if workspace_id is None:
                    self.exception = Exception('Unable to retrieve flow statistics because no workspace ID was available from watershed delineation.')
                    return False

                flow_stats = retrieve_flow_statistics(state_code, workspace_id)

            self.pour_point = save_pour_point(self.db_path, self.latitude, self.longitude, self.watershed_data, self.name, self.qris_description, basin_chars, flow_stats)

        except Exception as ex:
            self.exception = ex

        return True

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        if result:
            QgsMessageLog.logMessage(
                'Stream Stats API call "{name}" completed\n'
                'RandomTotal: {total} (with {iterations} '
                'iterations)'.format(
                    name=self.description(),
                    total=self.total,
                    iterations=self.iterations),
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Stream Stats API Request "{name}" not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Stream Statistics API Request "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.stream_stats_successfully_complete.emit(self.pour_point, self.add_to_map)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Stream Statistics "{name}" was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()


def transform_geometry(geometry, map_epsg: int, output_epsg: int):

    source_crs = QgsCoordinateReferenceSystem(map_epsg)
    dest_crs = QgsCoordinateReferenceSystem(output_epsg)
    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance().transformContext())
    return transform.transform(geometry)


# Makes all 4 api calls. Currently not working consistently due to time delays
def get_streamstats_data(lat: float, lon: float, get_basin_characteristics: bool, get_flow_statistics: bool, new_file_dir=None):
    state_code = get_state_from_coordinates(lat, lon)
    watershed_data = delineate_watershed(lat, lon, state_code, new_file_dir)
    workspace_id = watershed_data["workspaceID"]

    basin_characteristics = None
    if get_basin_characteristics is True:
        basin_characteristics = retrieve_basin_characteristics(state_code, workspace_id, new_file_dir)

    flow_statistics = None
    if get_flow_statistics is True:
        flow_statistics = retrieve_flow_statistics(state_code, workspace_id, new_file_dir)

    return (watershed_data, basin_characteristics, flow_statistics)


# Returns dictionary of watershed info based on coordinates and U.S. state
def delineate_watershed(lat, lon, rcode, file_dir=None):
    url = "https://prodweba.streamstats.usgs.gov/streamstatsservices/watershed.geojson"

    parameters = {
        "rcode": rcode,
        "xlocation": lon,
        "ylocation": lat,
        "crs": "4326",
        "includeparameters": "false",
        "includeflowtypes": "false",
        "includefeatures": "true",
        "simplify": "true"
    }

    response = requests.get(url, params=parameters)
    watershed_data = response.json()

    if file_dir is not None:
        save_json(watershed_data, file_dir, watershed_data["workspaceID"] + "_wats.geojson")
    return watershed_data


# Returns dictionary of river basin characteristics
def retrieve_basin_characteristics(rcode, workspace_id, file_dir=None):
    basin_chars_url = 'https://prodweba.streamstats.usgs.gov/streamstatsservices/parameters.json?rcode={0}&workspaceID={1}&includeparameters=true'
    url = basin_chars_url.format(rcode, workspace_id)
    response = requests.get(url)
    try:
        basin_data = response.json()
    except Exception as ex:
        raise Exception('Error retrieving basin characteristics') from ex
    if file_dir is not None:
        save_json(basin_data, file_dir, workspace_id + "_basin.json")
    return basin_data


# Returns dictionary of river flow stats
def retrieve_flow_statistics(rcode, workspace_id, file_dir=None):
    flow_stats_url = 'https://prodweba.streamstats.usgs.gov/streamstatsservices/flowstatistics.json?rcode={0}&workspaceID={1}&includeflowtypes=true'
    url = flow_stats_url.format(rcode, workspace_id)
    response = requests.get(url)
    try:
        flow_data = response.json()
    except Exception as ex:
        raise Exception('Error retrieving flow statistics') from ex

    if file_dir is not None:
        save_json(flow_data, file_dir, workspace_id + "_flow.json")
    return flow_data


# Saves dictionary to custom location
def save_json(dict, directory, file_name):
    with open(os.path.join(directory, file_name), 'w') as file:
        json.dump(dict, file)


# Uses coordinates to determine U.S. state using API
def get_state_from_coordinates(latitude: float, longitude: float):
    url = "https://nominatim.openstreetmap.org/reverse"
    parameters = {
        "lat": latitude,
        "lon": longitude,
        "format": "json"
    }

    response = requests.get(url, params=parameters)
    location_data = response.json()

    if location_data is None:
        raise Exception('Unable to determine US State. No response from Open Street Map.')
    elif 'error' in location_data:
        if 'geocode' in location_data['error']:
            return None
        else:
            raise Exception(location_data['error'])
    else:
        location_code = location_data["address"]["ISO3166-2-lvl4"]
        # Extracts state abbreviation from location code
        return location_code[location_code.index("-") + 1:]
