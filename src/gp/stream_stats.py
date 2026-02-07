import requests
import json
import os

from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsPointXY, QgsGeometry
from qgis.PyQt.QtCore import pyqtSignal

from ..model.pour_point import save_pour_point, PourPoint

MESSAGE_CATEGORY = 'QRiS_StreamStatsTask'


class StreamStats(QgsTask):

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    stream_stats_successfully_complete = pyqtSignal(PourPoint or None, bool)

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
            state_code, status = get_state_from_coordinates(self.latitude, self.longitude)

            if state_code is None:
                self.exception = Exception('Failed to determine US State of the point. Ensure that the point within the United States.')
                return False

            if self.isCanceled():
                return False

            self.watershed_data = delineate_watershed(self.latitude, self.longitude, state_code)
            
            # Legacy code expected 'workspaceID'. The new API architecture is stateless.
            # We pass the entire 'watershed_data' object (which is the SSHydroRequest) to subsequent calls.
            # workspace_id = self.watershed_data['workspaceID'] if 'workspaceID' in self.watershed_data else None
            # Note: The existing pour_point.save_pour_point logic likely expects certain keys in watershed_data.
            # We must ensure compatibility there or update save_pour_point as well.

            if self.isCanceled():
                return False

            basin_chars = None
            if self.get_basin_chars is True:
                # With new API, we pass the Delineate response structure, not a workspace ID
                basin_chars = retrieve_basin_characteristics(self.watershed_data)

            if self.isCanceled():
                return False

            flow_stats = None
            if self.get_flow_stats is True:
                # Flow stats are complex in new API. Attempting to retrieve via new workflow.
                try:
                    flow_stats = retrieve_flow_statistics(self.watershed_data)
                except Exception as e:
                    QgsMessageLog.logMessage(f'Flow Statistics failed/not supported yet: {e}', MESSAGE_CATEGORY, Qgis.Warning)
                    flow_stats = None

            self.pour_point = save_pour_point(self.db_path, self.latitude, self.longitude, self.watershed_data, self.name, self.qris_description, basin_chars, flow_stats)

        except Exception as ex:
            self.exception = ex
            return False

        return True

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        if result is True:
            QgsMessageLog.logMessage(
                'Stream Stats API call "{name}" completed\n'
                'RandomTotal: {total} (with {iterations} '
                'iterations)'.format(
                    name=self.description(),
                    total=self.total,
                    iterations=self.iterations),
                MESSAGE_CATEGORY, Qgis.Success)
            self.stream_stats_successfully_complete.emit(self.pour_point, self.add_to_map)
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
                # raise self.exception

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
    state_code, status = get_state_from_coordinates(lat, lon)
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
    if not rcode:
        raise Exception("Could not determine state code ('rcode') for the given coordinates.")

    # New API: SS-Delineate
    url = f"https://streamstats.usgs.gov/ss-delineate/v1/delineate/sshydro/{rcode}"

    parameters = {
        "lat": lat,
        "lon": lon
    }
    
    QgsMessageLog.logMessage(f'Delineating watershed via {url}', MESSAGE_CATEGORY, Qgis.Info)

    try:
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        watershed_data = response.json()
        # Response structure: {"stateAbbreviation": "RR", "bcrequest": { ... }}
        
        # Add a fake 'workspaceID' for backward compatibility if needed by save_pour_point or other consumers
        # The new API is stateless, so there is no ID, but we can generate one or mock it.
        if "workspaceID" not in watershed_data:
             watershed_data["workspaceID"] = "stateless_v1"

        # Backward Compatibility for 'featurecollection'
        # Old API returned 'featurecollection' at root. New API nests it in bcrequest.wsresp.featurecollection
        # and wraps it in an outer list [[{}, {}]].
        # save_pour_point expects: catchment['featurecollection'][1]['feature']['features'][0]['geometry']
        try:
            fc = watershed_data.get("bcrequest", {}).get("wsresp", {}).get("featurecollection", [])
            if fc and len(fc) > 0 and isinstance(fc[0], list):
                # Unwrap the outer list to match legacy structure of [points_obj, watershed_obj]
                watershed_data["featurecollection"] = fc[0]
        except Exception:
            # If structure is unexpected, don't crash here - let downstream handle or fail gracefully
            pass

    except Exception as e:
        error_msg = f"Error in delineate_watershed: {str(e)}"
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f". Response: {response.text}"
        raise Exception(error_msg)

    if file_dir is not None:
        save_json(watershed_data, file_dir, "watershed.json")
    return watershed_data


# Returns dictionary of river basin characteristics
def retrieve_basin_characteristics(delineation_data, file_dir=None):
    # New API: SS-Hydro
    url = "https://streamstats.usgs.gov/ss-hydro/v1/basin-characteristics/calculate"
    
    # Payload: The Delineation Response matches the SSHydroRequest schema
    payload = delineation_data.copy()
    
    # Ensure bcLabels is set (default '*' allows getting all available chars)
    if "bcrequest" in payload and "bcLabels" not in payload["bcrequest"]:
         payload["bcrequest"]["bcLabels"] = "*"

    QgsMessageLog.logMessage(f'Calculating Basin Characteristics via {url}', MESSAGE_CATEGORY, Qgis.Info)

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        basin_data = response.json()
    except Exception as ex:
        error_msg = f'Error retrieving basin characteristics: {str(ex)}'
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f". Response: {response.text}"
        raise Exception(error_msg)

    if file_dir is not None:
        save_json(basin_data, file_dir, "basin_chars.json")
    return basin_data


# Returns dictionary of river flow stats
def retrieve_flow_statistics(delineation_data, file_dir=None):
    # New API: NSS Services
    # This is a multi-step process and is significantly different from legacy.
    # Step 1: Get Regression Regions
    rr_url = "https://streamstats.usgs.gov/nssservices/regressionregions/bylocation"
    
    try:
        # Extract geometry from delineation_data
        # Structure: delineation_data["bcrequest"]["wsresp"]["featurecollection"][0][1]["feature"]
        # (Based on debug output observation)
        bcrequest = delineation_data.get("bcrequest", {})
        wsresp = bcrequest.get("wsresp", {})
        fc = wsresp.get("featurecollection", [])
        
        poly_feature = None
        if len(fc) > 0 and isinstance(fc[0], list) and len(fc[0]) > 1:
             poly_feature = fc[0][1].get("feature")
        
        if not poly_feature:
            raise Exception("Could not search for regression regions: Watershed geometry not found in response.")

        # Construct simple FeatureCollection for NSS
        rr_payload = {
            "type": "FeatureCollection",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features": [poly_feature]
        }
        
        QgsMessageLog.logMessage(f'Retrieving Regression Regions via {rr_url}', MESSAGE_CATEGORY, Qgis.Info)
        
        response = requests.post(rr_url, json=rr_payload)
        response.raise_for_status()
        rr_data = response.json()
        
        # NOTE: Full implementation of Flow Stats (Scenarios -> Estimate) requires extensive mapping 
        # of Basin Characteristics to Scenario variables. This is a large task.
        # For now, we return the Regression Regions info as a placeholder or throw a Not Implemented error
        # so the user knows this part is incomplete but doesn't crash the Delineation/Basin Chars.
        
        raise NotImplementedError("Full Flow Statistics computation via new API is not yet implemented.")

    except Exception as ex:
        error_msg = f'Error retrieving flow statistics: {str(ex)}'
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f". Response: {response.text}"
        # raise Exception(error_msg) 
        # Suppress fatal error for now, as Delineation/Basin Chars are more critical
        QgsMessageLog.logMessage(error_msg, MESSAGE_CATEGORY, Qgis.Warning)
        return {"error": "Flow Statistics not fully migrated to new API", "details": str(ex)}

    if file_dir is not None:
        save_json(flow_data, file_dir, "flow_stats.json")
    return flow_data


# Saves dictionary to custom location
def save_json(dict, directory, file_name):
    with open(os.path.join(directory, file_name), 'w') as file:
        json.dump(dict, file)


# Uses coordinates to determine U.S. state using API
def get_state_from_coordinates(latitude: float, longitude: float):
    """https://www.usgs.gov/streamstats/about"""

    # Get the states layer from the resources gpkg
    db_path = os.path.join(os.path.dirname(__file__), '..','..','resources', 'us_states.gpkg')

    # Load the layer
    states_layer = QgsVectorLayer(f"{db_path}|layername=states", "states", "ogr")

    # Create a point geometry
    point = QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude))

    # Intersect the point with the states layer
    states_layer.selectByRect(point.boundingBox())
    for feature in states_layer.selectedFeatures():
        if feature.geometry().intersects(point):
            return feature['STATE_ABBR'], feature['STATUS']
    
    return None, None
    
