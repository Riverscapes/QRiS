import os
from osgeo import ogr
import re
from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject
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

            # Set up Transform Context
            context = QgsProject.instance().transformContext()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GPKG'
            options.layerName = self.output_fc_name

            # Logic to set the write/update mode depending on if data source and/or layers are present
            if options.driverName == 'GPKG':
                if os.path.exists(self.output_path):
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                    if source_layer.dataProvider().subLayerCount() > 0:
                        options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
                else:
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            else:  # likely shapefile. Need to test for other formats and modify if needed.
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

            if self.mask_tuple is not None:
                clip_path = self.mask_tuple[0]
                clip_mask_id = self.mask_tuple[1]
                clip_layer = QgsVectorLayer(f'{clip_path}|layername=aoi_features')
                clip_layer.setSubsetString(f'mask_id = {clip_mask_id}')
                clip_transform = QgsCoordinateTransform(clip_layer.sourceCrs(), source_layer.sourceCrs(), QgsProject.instance().transformContext())
                clip_feat = clip_layer.getFeatures()
                clip_feat = next(clip_feat)
                clip_geom = clip_feat.geometry()
                clip_geom.transform(clip_transform)

                fields = source_layer.fields()
                writer = QgsVectorFileWriter.create(self.output_path, fields, source_layer.wkbType(), source_layer.sourceCrs(), context, options)

                for feat in source_layer.getFeatures():
                    if feat.geometry().intersects(clip_geom):
                        geom = feat.geometry()
                        geom = geom.intersection(clip_geom)
                        feat.setGeometry(geom)
                        writer.addFeature(feat)

                if writer.hasError() != QgsVectorFileWriter.NoError:
                    self.exception = Exception(str(writer.errorMessage()))
                    return False

                # Flush to disk
                del writer

            else:
                # Write vector layer to file
                error = QgsVectorFileWriter.writeAsVectorFormatV3(source_layer, self.output_path, context, options)

                if error[0] != QgsVectorFileWriter.NoError:
                    self.exception = Exception(str(error))
                    return False
            return True

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
