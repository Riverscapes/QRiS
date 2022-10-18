import requests
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
    on_task_complete = pyqtSignal(bool, int)

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
        self.inserted_discharge_records = 0

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

                count_before = self.get_discharge_record_count(curs)

                curs.executemany("""
                INSERT INTO stream_gage_discharges (
                    stream_gage_id,
                    measurement_date,
                    discharge,
                    discharge_code,
                    gage_height,
                    gage_height_code)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (stream_gage_id, measurement_date)
                DO UPDATE SET
                    discharge = excluded.discharge,
                    discharge_code = excluded.discharge_code,
                    gage_height = excluded.gage_height,
                    gage_height_code = excluded.gage_height_code""", sql_data)

                conn.commit()

                count_after = self.get_discharge_record_count(curs)

                self.inserted_discharge_records = count_after - count_before

        except Exception as ex:
            self.exception = ex
            return False

        return True

    def get_discharge_record_count(self, curs):

        curs.execute('SELECT count(*) FROM stream_gage_discharges')
        return curs.fetchone()[0]

    # def get_gage_data(self):

    #     # url = BASE_REQUEST.format(self.min_lng, self.min_lat, self.max_lng, self.max_lat)
    #     params = {
    #         'format': 'rdb',
    #         'site_no': '02085070',  # self.site_code,
    #         # 'begin_date': self.start_date,
    #         # 'end_date': self.end_date
    #     }
    #     response = requests.get(BASE_REQUEST, params=params)

    #     if response.status_code == 200:
    #         csv_raw = [line for line in response.text.split('\n') if not (line.startswith('#') or line.startswith('5s'))]
    #         return csv.DictReader(csv_raw, delimiter='\t')
    #     else:
    #         raise Exception(response)

    # def save_gage_data(self, gage_data):

    #     conn = sqlite3.connect(self.db_path)
    #     curs = conn.cursor()

    #     curs.execute('SELECT fid FROM stream_gages WHERE site_name = ?', [self.site_code])
    #     gage_id = curs.fetchone()[0]

    #     for data in gage_data:
    #         print('none')

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        if result:
            QgsMessageLog.logMessage('Discharge Download Complete. {self.inserted_discharge_records} records downloaded.', MESSAGE_CATEGORY, Qgis.Success)
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

        self.on_task_complete.emit(result, self.inserted_discharge_records)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Stream Statistics "{name}" was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
