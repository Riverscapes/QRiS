import os
import json
from typing import List

from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsDataProvider, QgsVectorLayer, QgsFields, QgsWkbTypes, QgsCoordinateTransformContext, QgsField, QgsVectorFileWriter, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject
from qgis.PyQt.QtCore import pyqtSignal, QVariant

from .import_feature_class import ImportFieldMap
from ..gp.feature_class_functions import layer_path_parser

MESSAGE_CATEGORY = 'QRiS_ImportTemporaryLayer'


class ImportTemporaryLayer(QgsTask):
    """
    Use only for qgis temporary layers. All others use ImportFeatureClass instead.

    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    import_complete = pyqtSignal(bool, int, int, int)

    def __init__(self, source_layer: QgsVectorLayer, dest_path: str, attributes: dict=None, field_map: List[ImportFieldMap]=None, clip_mask_id=None, attribute_filter: str=None, proj_gpkg=None):
        super().__init__(f'Import Temporary Layer', QgsTask.CanCancel)

        self.source_layer = source_layer.clone()
        self.clip_mask_id = clip_mask_id
        self.dest_path = dest_path
        self.attributes = attributes
        self.proj_gpkg = proj_gpkg
        self.field_map = field_map
        self.attribute_filter = attribute_filter

        self.in_feats = 0
        self.out_feats = 0
        self.skipped_feats = 0

    def run(self):

        self.setProgress(0)

        try:

            dst_path, dst_layer_name, _dst_layer_id = layer_path_parser(self.dest_path)

            base_path = os.path.dirname(dst_path)
            if not os.path.exists(base_path):
                os.makedirs(base_path)

            # Set up Transform Context
            context = QgsProject.instance().transformContext()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GPKG'
            options.layerName = dst_layer_name

            epgs_4326 = QgsCoordinateReferenceSystem('EPSG:4326')
            out_transform = QgsCoordinateTransform(self.source_layer.sourceCrs(), epgs_4326, QgsProject.instance().transformContext())

            # Logic to set the write/update mode depending on if data source and/or layers are present
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            if options.driverName == 'GPKG':
                if os.path.exists(dst_path):
                    output_layer = QgsVectorLayer(dst_path)
                    sublayers = [subLayer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1] for subLayer in output_layer.dataProvider().subLayers()]
                    if options.layerName not in sublayers:
                        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                else:
                    # If the file does not exist, we need to create it
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

            # add the event_id field to the source layer
            if self.attributes is not None:
                fields = []
                for field_name in self.attributes.keys():
                    field = QgsField(field_name, QVariant.Int)
                    fields.append(field)
                self.source_layer.dataProvider().addAttributes(fields)
                self.source_layer.updateFields()

            if self.clip_mask_id is not None:
                clip_layer = QgsVectorLayer(f'{self.proj_gpkg}|layername=aoi_features')
                clip_layer.setSubsetString(f'mask_id = {self.clip_mask_id}')
                clip_transform = QgsCoordinateTransform(clip_layer.sourceCrs(), self.source_layer.sourceCrs(), QgsProject.instance().transformContext())
                clip_feat = clip_layer.getFeatures()
                clip_feat = next(clip_feat)
                clip_geom = clip_feat.geometry()
                clip_geom.transform(clip_transform)

            if self.attribute_filter is not None:
                self.source_layer.selectByExpression(self.attribute_filter)

            self.in_feats = self.source_layer.featureCount()
            
            # add the metadata field to the source layer
            # Check first
            if self.source_layer.fields().lookupField('metadata') == -1:
                field = QgsField('metadata', QVariant.String)
                self.source_layer.dataProvider().addAttributes([field])
                self.source_layer.updateFields()
            
            # make sure any direct copy fields are in the output layer
            if self.field_map is not None:
                for field_map in self.field_map:
                    if field_map.direct_copy is True:
                        if self.source_layer.fields().lookupField(field_map.dest_field) == -1:
                            field = QgsField(field_map.dest_field, QVariant.String)
                            self.source_layer.dataProvider().addAttributes([field])
                            self.source_layer.updateFields()

            self.source_layer.startEditing()
            self.out_feats = 0
            for feat in self.source_layer.getFeatures():
                if self.attributes is not None:
                    for field_name, field_value in self.attributes.items():
                        feat[field_name] = field_value
                if self.field_map is not None:
                    metadata = {}
                    field_map: ImportFieldMap = None
                    for field_map in self.field_map:
                        value = feat[field_map.src_field]
                        # change empty stringd to None
                        if value == '':
                            value = None
                        if field_map.direct_copy is True:
                            # we need to copy the value directly to the output field
                            feat[field_map.dest_field] = value
                            continue
                        # if field_map.dest_field == 'display_label':
                        #     value = str(feat.id()) if field_map.src_field == src_fid_field_name else value
                        if field_map.dest_field is not None:
                            if field_map.parent is not None:
                                # this is a child field. we need to add it to the parent
                                if field_map.parent not in metadata:
                                    metadata[field_map.parent] = {}
                                metadata[field_map.parent].update({field_map.dest_field: value})
                            else:
                                metadata.update({field_map.dest_field: value})
                        if field_map.map is not None:
                            # there is a value map. we need to map the value to the output fields in the metadata
                            value_map: dict = field_map.map[value]
                            if field_map.parent is not None:
                                # this is a child field. we need to add it to the parent
                                if field_map.parent not in metadata:
                                    metadata[field_map.parent] = {}
                                for dest_field, out_value in value_map.items():
                                    metadata[field_map.parent].update({dest_field: out_value})
                            else:
                                for dest_field, out_value in value_map.items():
                                    metadata.update({dest_field: out_value})
                    if metadata:
                        feat['metadata'] = json.dumps(metadata)
                
                geom = feat.geometry()
                if self.clip_mask_id is not None:
                    geom = geom.intersection(clip_geom)
                geom.transform(out_transform)
                feat.setGeometry(geom)
                self.source_layer.updateFeature(feat)
                self.out_feats += 1
            self.source_layer.commitChanges()

            # Write vector layer to file
            error = QgsVectorFileWriter.writeAsVectorFormatV3(self.source_layer, dst_path, context, options)

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

        self.import_complete.emit(result, self.in_feats, self.out_feats, self.skipped_feats)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Feature Class copy was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
