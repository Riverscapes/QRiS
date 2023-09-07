import os

from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsDataProvider, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject
from qgis.PyQt.QtCore import pyqtSignal, QVariant

from ..model.db_item import DBItem

MESSAGE_CATEGORY = 'QRiS_ImportTemporaryLayer'


class ImportTemporaryLayer(QgsTask):
    """
    Use only for qgis temporary layers. All others use ImportFeatureClass instead.

    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    import_complete = pyqtSignal(bool)

    def __init__(self, source_layer: str, output_dataset_path: str, output_layer_name: str, id_field: str = None, id_value: str = None, mask_clip_id=None, proj_gpkg=None):
        super().__init__(f'Import Temporary Layer', QgsTask.CanCancel)

        self.source_layer = source_layer.clone()
        self.mask_clip_id = mask_clip_id
        self.output_path = output_dataset_path
        self.output_fc_name = output_layer_name
        self.id_field = id_field
        self.id_value = id_value
        self.proj_gpkg = proj_gpkg

    def run(self):

        self.setProgress(0)

        try:
            output_dir = os.path.dirname(self.output_path)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            # Set up Transform Context
            context = QgsProject.instance().transformContext()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GPKG'
            options.layerName = self.output_fc_name

            epgs_4326 = QgsCoordinateReferenceSystem('EPSG:4326')
            out_transform = QgsCoordinateTransform(self.source_layer.sourceCrs(), epgs_4326, QgsProject.instance().transformContext())

            # Logic to set the write/update mode depending on if data source and/or layers are present
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            if options.driverName == 'GPKG':
                if os.path.exists(self.output_path):
                    output_layer = QgsVectorLayer(self.output_path)
                    sublayers = [subLayer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1] for subLayer in output_layer.dataProvider().subLayers()]
                    if options.layerName not in sublayers:
                        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            # add the event_id field to the source layer
            if self.id_field is not None:
                field = QgsField(self.id_field, QVariant.Int)
                self.source_layer.dataProvider().addAttributes([field])
                self.source_layer.updateFields()

            if self.mask_clip_id is not None:
                clip_layer = QgsVectorLayer(f'{self.proj_gpkg}|layername=aoi_features')
                clip_layer.setSubsetString(f'mask_id = {self.mask_clip_id}')
                clip_transform = QgsCoordinateTransform(clip_layer.sourceCrs(), self.source_layer.sourceCrs(), QgsProject.instance().transformContext())
                clip_feat = clip_layer.getFeatures()
                clip_feat = next(clip_feat)
                clip_geom = clip_feat.geometry()
                clip_geom.transform(clip_transform)

            self.source_layer.startEditing()
            for feat in self.source_layer.getFeatures():
                if self.id_field is not None:
                    feat[self.id_field] = self.id_value
                geom = feat.geometry()
                if self.mask_clip_id is not None:
                    geom = geom.intersection(clip_geom)
                geom.transform(out_transform)
                feat.setGeometry(geom)
                self.source_layer.updateFeature(feat)
            self.source_layer.commitChanges()

            # Write vector layer to file
            error = QgsVectorFileWriter.writeAsVectorFormatV3(self.source_layer, self.output_path, context, options)

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
                # raise self.exception

        self.import_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Feature Class copy was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
