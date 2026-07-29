import json
import tempfile
import webbrowser

from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from ..compat import MESSAGE_LEVEL_CRITICAL, MESSAGE_LEVEL_SUCCESS, MESSAGE_LEVEL_WARNING, QGSTASK_CAN_CANCEL
from ..QRiS.settings import CONSTANTS, Settings
from .watershed_attribute_api import QueryMonster

# from .report_creation.qris_report import QRiSReport

MESSAGE_CATEGORY = "QRiS_WatershedAttributesTask"


class WatershedAttributes(QgsTask):
    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    process_complete = pyqtSignal(str, bool)

    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    def __init__(self, latitude: float, longitude: float, format_as_report: bool):
        super().__init__(f"Watershed Attributes API Request at {longitude}, {latitude}", QGSTASK_CAN_CANCEL)
        # self.duration = duration
        self.format_as_report = False  # format_as_report
        self.latitude = latitude
        self.longitude = longitude
        self.output_path = None
        self.total = 0
        self.iterations = 0
        self.exception = None

    def run(self):
        """Heavy lifting and periodically check for isCanceled() and gracefully abort.
        Must return True or False. Raising exceptions will crash QGIS"""

        try:
            # Call watershed attribute API with coordinates
            api = QueryMonster(CONSTANTS["watershedAttributeApiUrl"], CONSTANTS["watershedAttributeApiKey"])
            query = """
            query project_query($lat: Float!, $lng: Float!) {
                pointMetrics(lat: $lat, lng: $lng) {
                    HUC12 {
                    id
                    name
                    }
                    upstreamMetrics
                    HUC12Metrics
                }
            }"""
            Settings().log(f"Watershed Attribute API request at {self.latitude}, {self.longitude}\n\n{query}")

            response = api.run_query(query, {"lng": self.longitude, "lat": self.latitude})

            if response is None:
                raise Exception(f"No response from API\n{query}")

            self.output_path = tempfile.NamedTemporaryFile(delete=False).name
            self.output_path += ".html" if self.format_as_report else ".json"

            if self.format_as_report:
                _google_maps_api_key = CONSTANTS["google_api_key"] if "google_api_key" in CONSTANTS else None
                # QRiSReport(google_maps_api_key, self.longitude, self.latitude, response, self.output_path)
            else:
                with open(self.output_path, "w") as f:
                    json.dump(self.output_path, f)

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
        if result:
            Settings().log("Watershed Attributes request completed", MESSAGE_LEVEL_SUCCESS)
            webbrowser.open("file://" + self.output_path)
        else:
            if self.exception is None:
                Settings().log("Watershed Attribute Request unsuccessful but without exception", MESSAGE_LEVEL_WARNING)
            else:
                Settings().log(f"Watershed Attribute API Request Exception: {self.exception}", MESSAGE_LEVEL_CRITICAL)
                # raise self.exception

        self.process_complete.emit(self.output_path, result)

    def cancel(self):
        Settings().log(f'Watershed Attributes "{self.description()}" was canceled', MESSAGE_LEVEL_WARNING)
        super().cancel()
