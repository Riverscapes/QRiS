import json
import sqlite3

from osgeo import ogr
import pandas as pd
from qgis.core import QgsFeature, QgsGeometry, QgsTask
from qgis.PyQt.QtCore import pyqtSignal
import requests

from ..compat import MESSAGE_LEVEL_CRITICAL, MESSAGE_LEVEL_SUCCESS, MESSAGE_LEVEL_WARNING, QGSTASK_CAN_CANCEL
from ..lib.climate_engine import CLIMATE_ENGINE_API, get_api_key
from ..model.project import Project
from ..QRiS.settings import Settings

DOWNLOAD_TIMEOUT = 120  # seconds (2 minutes)

AREA_REDUCER = {"Mean": "mean", "Median": "median", "Max": "max", "Min": "min"}


class DownloadClimateEngineTimeseriesTask(QgsTask):
    """
    Task to download data from Climate Engine.
    """

    # Signal to notify when done
    download_complete = pyqtSignal(bool)

    def __init__(self, qris_project: Project, name: str, dataset: str, variables: list[str], start_date: str, end_date: str, features: ogr.Feature, area_reducer: str = "mean"):
        super().__init__("Download Climate Engine Task", QGSTASK_CAN_CANCEL)

        self.qris_project = qris_project
        self.name = name
        self.dataset = dataset
        self.variables = [variables] if isinstance(variables, str) else variables
        self.start_date = start_date
        self.end_date = end_date
        self.features = features
        self.area_reducer = area_reducer

    def run(self):
        """
        Run the task.
        """

        self.setProgress(0)

        try:
            api_key = get_api_key()
            if api_key is None:
                return None

            time_series_ids = {}

            steps = len(self.features)
            current_step = 0

            for feature in self.features:
                coordinates = []
                if isinstance(feature, QgsFeature):
                    geometry: QgsGeometry = feature.geometry()
                    feature_id = feature.id()
                    if geometry.isMultipart():
                        part_coordinates = []
                        for part in geometry.asMultiPolygon():
                            for pt in part[0]:
                                part_coordinates.append([pt.x(), pt.y()])
                        coordinates.append(part_coordinates)
                    else:
                        for pt in geometry.asPolygon()[0]:
                            coordinates.append([pt.x(), pt.y()])
                else:
                    feature: ogr.Feature
                    geometry: ogr.Geometry = feature.GetGeometryRef()
                    feature_id = feature.GetFID()
                    if geometry.GetGeometryName() == "POLYGON":
                        for i in range(geometry.GetPointCount()):
                            pt = geometry.GetPoint(i)
                            coordinates.append([pt[0], pt[1]])
                    else:
                        for i in range(geometry.GetGeometryCount()):
                            part: ogr.Geometry = geometry.GetGeometryRef(i)
                            part_coordinates = []
                            for j in range(part.GetPointCount()):
                                pt = part.GetPoint(j)
                                part_coordinates.append([pt[0], pt[1]])
                            coordinates.append(part_coordinates)

                params = {"dataset": self.dataset, "variable": self.variables, "area_reducer": self.area_reducer, "start_date": self.start_date, "end_date": self.end_date, "coordinates": f"[{coordinates}]"}

                url = f"{CLIMATE_ENGINE_API}/timeseries/native/coordinates"
                headers = {"accept": "application/json", "Authorization": api_key}
                response = requests.get(url, params=params, headers=headers, timeout=DOWNLOAD_TIMEOUT)
                response.raise_for_status()
                response_content = response.json()

                [response_data] = response_content.get("Data", None)
                data = response_data.get("Data", None)

                if data is None:
                    Settings.log(f"No data for feature {feature_id} for one or more {self.variables} in {self.dataset}", MESSAGE_LEVEL_WARNING)
                    continue

                df = pd.DataFrame(data)

                with sqlite3.connect(self.qris_project.project_file) as conn:
                    cursor = conn.cursor()

                    for column in df.columns:
                        if column == "Date":
                            continue
                        splits = column.split(" (")
                        if len(splits) == 1:
                            variable = column
                            units = ""
                        else:
                            variable, units = splits
                            units = units.replace(")", "")
                        df_values = df[["Date", column]]
                        df_values = df_values.set_index("Date")
                        values = list(df_values.itertuples(name=None))
                        machine_name = f"{self.dataset} {variable}"
                        if machine_name in time_series_ids:
                            time_series_id = time_series_ids[machine_name]
                        else:
                            metadata = {
                                "units": units,
                                "start_date": self.start_date.strftime("%Y-%m-%d"),
                                "end_date": self.end_date.strftime("%Y-%m-%d"),
                                "description": variable,
                                "dataset": self.dataset,
                                "variable": variable,
                                "area_reducer": self.area_reducer,
                            }
                            cursor.execute("INSERT INTO time_series (name, source, url, metadata) VALUES (?, ?, ?, ?)", (self.name, "Climate Engine", "https://www.climateengine.org/", json.dumps(metadata)))
                            time_series_id = cursor.lastrowid
                            time_series_ids[machine_name] = time_series_id
                        cursor.executemany("INSERT INTO sample_frame_time_series (sample_frame_fid, time_series_id, time_value, value) VALUES (?, ?, ?, ?)", [(feature_id, time_series_id, date, value) for date, value in values])

                current_step += 1
                self.setProgress(100 * current_step / steps)

            with sqlite3.connect(self.qris_project.project_file, isolation_level=None) as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            return True

        except requests.exceptions.HTTPError as e:
            Settings.log(f"HTTP error occurred: {e}", MESSAGE_LEVEL_CRITICAL)
            return False
        except Exception as e:
            Settings.log(f"Error downloading data: {e}", MESSAGE_LEVEL_CRITICAL)
            return False

    def finished(self, result):
        """
        This function is automatically called when the task has completed (successfully or not).
        """
        if result:
            Settings.log("Download completed successfully.", MESSAGE_LEVEL_SUCCESS)
        else:
            Settings.log("Download failed.", MESSAGE_LEVEL_CRITICAL)

        self.download_complete.emit(result)

    def cancel(self):
        """
        This function is automatically called when the task is canceled.
        """
        Settings.log("Download canceled.", MESSAGE_LEVEL_WARNING)
        super().cancel()

        Settings.log("Create New QRIS Project was canceled.", MESSAGE_LEVEL_WARNING)
        super().cancel()
