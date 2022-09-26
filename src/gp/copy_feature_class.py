import os
from osgeo import ogr
import re
from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal
from osgeo.gdal import Warp, WarpOptions, VectorTranslate, VectorTranslateOptions
from ..model.db_item import DBItem

MESSAGE_CATEGORY = 'QRiS_CopyFeatureClassTask'


class CopyFeatureClass(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    copy_complete = pyqtSignal(bool)

    def __init__(self, source_path: str, mask_tuple, output_ds: str, output_fc_name: str):
        super().__init__(f'Copy Raster Task', QgsTask.CanCancel)

        self.source_path = source_path
        self.mask_tuple = mask_tuple
        self.output_path = output_ds
        self.output_fc_name = output_fc_name

    def run(self):
        """
        Originally intended to use this VectorTranslate method
        https://gdal.org/development/rfc/rfc59.1_utilities_as_a_library.html#swig-bindings-python-java-c-perl-changes

        But ended up using this ogr method
        https://subscription.packtpub.com/book/application-development/9781787124837/3/ch03lvl1sec58/exporting-a-layer-to-the-geopackage-format
        """

        # You can use this WarpOptions to get a list of the possible options
        # wo = WarpOptions(format: 'GTiff', cutl)

        # user defined callback object
        es_obj = {}

        # kwargs = {
        #     'format': 'GTiff',
        #     'callback': self.progress_callback,
        #     'callback_data': es_obj
        # }

        # if self.mask_tuple is not None:
        #     kwargs['cutlineDSName'] = self.mask_tuple[0]
        #     kwargs['cutlineLayer'] = 'mask_features'
        #     kwargs['cutlineWhere'] = 'mask_id = {}'.format(self.mask_tuple[1])

        # QgsMessageLog.logMessage(f'Started copy raster request', MESSAGE_CATEGORY, Qgis.Info)

        self.setProgress(0)

        # options = VectorTranslateOptions(dstSRS='EPSG:4326')

        try:
            output_dir = os.path.dirname(self.output_path)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            driver = ogr.GetDriverByName("GPKG")
            if not os.path.isfile(self.output_path):
                ds = driver.CreateDataSource(self.output_path)
            else:
                ds = driver.Open(self.output_path, 1)

            if re.match(r'.*\.shp', self.source_path) is not None:
                sf1 = ogr.Open(self.source_path)
            else:
                src_ds, src_layer = self.source_path.split('|layername=')
                sf1 = ogr.Open(src_ds)

            if sf1.GetLayerCount() > 1:
                sf_lyr1 = sf1.GetLayerByName(src_layer)
            else:
                sf_lyr1 = sf1.GetLayer(0)

            out_lyr = ds.CopyLayer(sf_lyr1, self.output_fc_name, [])
            if out_lyr is None:
                raise Exception('Failed to Copy Feature Class.')

            # ds = VectorTranslate(
            #     self.output_path,
            #     self.source_path,
            #     options=VectorTranslateOptions(
            #         # SQLStatement='SELECT * FROM mytable',
            #         layerName=self.output_fc_name,
            #         format='GPKG',
            #         callback=self.progress_callback,
            #         callback_data=es_obj
            #     )
            # )

            if ds is None:
                raise Exception('Error copying feature class')

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
            QgsMessageLog.logMessage('Copy Feature Class completed', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Feature Class copy not successful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Feature Class copy exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.copy_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Feature Class copy was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
