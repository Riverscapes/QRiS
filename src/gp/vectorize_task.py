from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal


from .vectorize import raster_to_polygon

Path = str

MESSAGE_CATEGORY = 'QRiS_VectorizeClassTask'


class VectorizeTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_complete = pyqtSignal(bool)

    def __init__(self, raster_path: Path, out_gpkg: Path, out_layer_name: str, raster_value: float, simplify_tolerance: float = 0.00008, smoothing_offset: float = 0.25, polygon_min_size: float = 9.0):
        super().__init__(f'Vectorize Task', QgsTask.CanCancel)

        self.raster_path = raster_path
        self.out_gpkg = out_gpkg
        self.out_layer_name = out_layer_name
        self.raster_value = raster_value
        self.simplify_tolerance = simplify_tolerance
        self.smoothing_offset = smoothing_offset
        self.polygon_min_size = polygon_min_size

    def run(self):
        """
        Vectorize
        """
        try:
            raster_to_polygon(self.raster_path, self.out_gpkg, self.out_layer_name, self.raster_value, self.simplify_tolerance, self.smoothing_offset, self.polygon_min_size)
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
            QgsMessageLog.logMessage('Metrics Complete', MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Vectorize was unsuccessful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Vectorize exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.on_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Vectorize polygon was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
