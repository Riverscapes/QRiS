import os
from osgeo import ogr
import re
from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import pyqtSignal
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

        # if self.mask_tuple is not None:
        #     kwargs['cutlineDSName'] = self.mask_tuple[0]
        #     kwargs['cutlineLayer'] = 'mask_features'
        #     kwargs['cutlineWhere'] = 'mask_id = {}'.format(self.mask_tuple[1])

        self.setProgress(0)

        try:
            output_dir = os.path.dirname(self.output_path)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            source_layer = QgsVectorLayer(self.source_path)
            source_layer.crs

            if self.mask_tuple is not None:
                # TODO clip layer features by mask here
                pass

            # TODO review how we want to handle crs
            context = QgsCoordinateTransformContext()
            ref_crs = source_layer.sourceCrs()
            dest_crs = source_layer.sourceCrs()  # QgsCoordinateReferenceSystem("EPSG:4326")
            context.addCoordinateOperation(ref_crs, dest_crs, "")

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GPKG'
            options.layerName = self.output_fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            # options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

            error = QgsVectorFileWriter.writeAsVectorFormatV3(source_layer, self.output_path, context, options)

            if error[0] == QgsVectorFileWriter.NoError:
                return True
            else:
                self.exception = Exception(str(error))
                return False

        except Exception as ex:
            self.exception = ex
            return False

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
