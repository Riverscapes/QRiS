from math import radians, cos, sin, asin, sqrt, degrees

from osgeo import gdal, osr

from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal

from ..model.db_item import DBItem

MESSAGE_CATEGORY = 'QRiS_HillshadeTask'


class Hillshade(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    hillshade_complete = pyqtSignal(bool)

    def __init__(self, source_path: str, output_path: str):
        super().__init__(f'Hillshade Task', QgsTask.CanCancel)

        self.dem = source_path
        self.output_path = output_path

    def run(self):
        """
        https://gdal.org/python/osgeo.gdal-module.html#WarpOptions
        https://gis.stackexchange.com/questions/278627/using-gdal-warp-and-gdal-warpoptions-of-gdal-python-api
        """

        # You can use this WarpOptions to get a list of the possible options
        # wo = WarpOptions(format: 'GTiff', cutl)

        # user defined callback object
        es_obj = {}

        kwargs = {
            'format': 'GTiff',
            'callback': self.progress_callback,
            'callback_data': es_obj
        }

        # set the z factor for the hillshade
        zfactor = 1
        src = gdal.Open(self.dem)
        srs = osr.SpatialReference(wkt=src.GetProjection())
        epsg = int(srs.GetAttrValue('AUTHORITY', 1))
        if epsg == 4326:
            ulx, xres, _xskew, uly, _yskew, yres = src.GetGeoTransform()
            _lrx = ulx + (src.RasterXSize * xres)
            lry = uly + (src.RasterYSize * yres)
            length_km = haversine(uly, ulx, lry, ulx)
            length_deg = uly - lry
            zfactor = (length_km * 1000) / length_deg
        src = None

        QgsMessageLog.logMessage(f'Started hillshade request', MESSAGE_CATEGORY, Qgis.Info)
        self.setProgress(0)

        try:
            gdal.DEMProcessing(self.output_path, self.dem, 'hillshade', scale=zfactor, creationOptions=["COMPRESS=DEFLATE"], **kwargs)
        except Exception as ex:
            self.exception = ex
            return False

        return True

    def progress_callback(self, complete, message, unknown):
        self.setProgress(complete * 100)

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            QgsMessageLog.logMessage('Hillshade completed', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Hillshade not successful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Hillshade Exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.hillshade_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Hillshade was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()


def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    """[summary]
    Great circle distance calculation
    https://rosettacode.org/wiki/Haversine_formula#Python
    Arguments:
        lat1 ([float]): latitude 1 (in degrees)
        lon1 ([float]): longitude 1 (in degrees)
        lat2 ([float]): latitude 2 (in degrees)
        lon2 ([float]): longitude 2 (in degrees)
    Returns:
        distance ([float]) -- distance in Km
    """
    R = 6372.8  # Earth radius in kilometers

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat / 2)**2 + cos(lat1) * cos(lat2) * sin(dLon / 2)**2
    c = 2 * asin(sqrt(a))

    return R * c
