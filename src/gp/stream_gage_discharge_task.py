import requests
import json
import os
import csv
import sqlite3
from io import StringIO
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsTask, QgsMessageLog, Qgis
from ..model.pour_point import save_pour_point, PourPoint
from qgis.PyQt.QtCore import pyqtSignal

MESSAGE_CATEGORY = 'QRiS_StreamGageTask'

# https://waterservices.usgs.gov/rest/Site-Service.html
# https://waterservices.usgs.gov/rest/Site-Test-Tool.html
# https://github.com/ENV859/UsingAPIs/blob/master/1-NWIS-discharge-data-as-API.ipynb
BASE_REQUEST = 'http://waterdata.usgs.gov/nwis/uv'


class StreamGageDischargeTask(QgsTask):

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_task_complete = pyqtSignal(PourPoint or None, bool)

    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    def __init__(self, db_path: str, site_code, site_id, start_date, end_date):
        super().__init__(f'Stream Gage Discharge API Request for {site_code}', QgsTask.CanCancel)
        # self.duration = duration
        self.db_path = db_path
        self.site_code = site_code
        self.site_id = site_id
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        """Heavy lifting and periodically check for isCanceled() and gracefully abort.
        Must return True or False. Raising exceptions will crash QGIS"""

        QgsMessageLog.logMessage(f'Started Stream Gage Discharge API Request ', MESSAGE_CATEGORY, Qgis.Info)

        try:
            params = {
                'format': 'rdb',
                'site_no': '02085070',  # self.site_code,
                # 'begin_date': self.start_date,
                # 'end_date': self.end_date
            }
            response = requests.get(BASE_REQUEST, params=params)

            if response.status_code == 200:
                csv_raw = [line for line in response.text.split('\n') if not (line.startswith('#') or line.startswith('5s'))]
                csv_data = csv.DictReader(csv_raw, delimiter='\t')
                # agency_cd,site_no,datetime,tz_cd,89062_00060,89062_00060_cd,89063_00065,89063_00065_cd
                sql_data = [(
                    self.site_id,
                    row['datetime'],
                    row['89062_00060'],
                    row['89062_00060_cd'],
                    row['89063_00065'],
                    row['89063_00065_cd']) for row in csv_data]

                conn = sqlite3.connect(self.db_path)
                curs = conn.cursor()
                curs.executemany("""INSERT INTO stream_gage_discharges (
                    stream_gage_id,
                    measurement_date,
                    discharge,
                    discharge_code,
                    gage_height,
                    gage_height_code) VALUES (?, ?, ?, ?, ?, ?)""", sql_data)

                conn.commit()

        except Exception as ex:
            self.exception = ex
            return False

        return True

    def get_gage_data(self):

        # url = BASE_REQUEST.format(self.min_lng, self.min_lat, self.max_lng, self.max_lat)
        params = {
            'format': 'rdb',
            'site_no': '02085070',  # self.site_code,
            # 'begin_date': self.start_date,
            # 'end_date': self.end_date
        }
        response = requests.get(BASE_REQUEST, params=params)

        if response.status_code == 200:
            csv_raw = [line for line in response.text.split('\n') if not (line.startswith('#') or line.startswith('5s'))]
            return csv.DictReader(csv_raw, delimiter='\t')
        else:
            raise Exception(response)

    def save_gage_data(self, gage_data):

        conn = sqlite3.connect(self.db_path)
        curs = conn.cursor()

        curs.execute('SELECT fid FROM stream_gages WHERE site_name = ?', [self.site_code])
        gage_id = curs.fetchone()[0]

        for data in gage_data:
            print('none')

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
