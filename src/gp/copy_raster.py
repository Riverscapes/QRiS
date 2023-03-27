import math
from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal
from osgeo.gdal import Warp, WarpOptions
from ..model.db_item import DBItem

MESSAGE_CATEGORY = 'QRiS_CopyRasterTask'


class CopyRaster(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    copy_raster_complete = pyqtSignal(bool)

    def __init__(self, source_path: str, mask_tuple, output_path: str):
        super().__init__(f'Copy Raster Task', QgsTask.CanCancel)

        self.source_path = source_path
        self.mask_tuple = mask_tuple
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

        if self.mask_tuple is not None:
            kwargs['cutlineDSName'] = self.mask_tuple[0]
            kwargs['cutlineLayer'] = 'aoi_features'
            kwargs['cutlineWhere'] = 'mask_id = {}'.format(self.mask_tuple[1])
            kwargs['cropToCutline'] = True

        QgsMessageLog.logMessage(f'Started copy raster request', MESSAGE_CATEGORY, Qgis.Info)

        self.setProgress(0)

        try:
            Warp(self.output_path, self.source_path, **kwargs)

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
            QgsMessageLog.logMessage('Copy Raster completed', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Raster Copy not successful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Raster Copy Exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.copy_raster_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Raster Copy was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
