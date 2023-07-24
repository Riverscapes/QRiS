import json

from osgeo import ogr, osr

from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal

from ..gp.feature_class_functions import layer_path_parser

MESSAGE_CATEGORY = 'QRiS_ImportFeatureClassTask'


class ImportFeatureClass(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    import_complete = pyqtSignal(bool, int, int)

    def __init__(self, source_path: str, dest_path: str, output_id_field: str, output_id: int, field_map: dict = None, clip_mask_id=None):
        super().__init__(f'Import Feature Class Task', QgsTask.CanCancel)

        self.source_path = source_path
        self.clip_mask_id = clip_mask_id
        self.output_path = dest_path
        self.field_map = field_map
        self.output_id_field = output_id_field
        self.output_id = output_id
        self.in_feats = 0
        self.out_feats = 0

    def run(self):

        self.setProgress(0)

        try:
            src_path, _src_layer_name, src_layer_id = layer_path_parser(self.source_path)
            src_dataset = ogr.Open(src_path)
            src_layer = src_dataset.GetLayer(src_layer_id)
            src_srs = src_layer.GetSpatialRef()
            src_fid_field_name = src_layer.GetFIDColumn()
            self.in_feats = src_layer.GetFeatureCount()

            dst_path, dst_layer_name, _dst_layer_id = layer_path_parser(self.output_path)
            gpkg_driver = ogr.GetDriverByName('GPKG')
            dst_dataset = gpkg_driver.Open(dst_path, 1)
            dst_layer = dst_dataset.GetLayerByName(dst_layer_name)
            dst_srs = dst_layer.GetSpatialRef()
            dst_layer_def = dst_layer.GetLayerDefn()

            clip_geom = None
            if self.clip_mask_id is not None:
                clip_layer = dst_dataset.GetLayer('aoi_features')
                clip_layer.SetAttributeFilter(f'mask_id = {self.clip_mask_id}')
                clip_feat = clip_layer.GetNextFeature()
                clip_geom = clip_feat.GetGeometryRef()

            transform = osr.CoordinateTransformation(src_srs, dst_srs)

            self.out_feats = 0
            for src_feature in src_layer:
                geom = src_feature.GetGeometryRef()
                geom.Transform(transform)
                if clip_geom is not None:
                    geom = clip_geom.Intersection(geom)
                    if geom.IsEmpty() or geom.GetArea() == 0.0:
                        continue

                # Remove M and Z values
                if geom.Is3D():
                    geom.FlattenTo2D()
                if geom.IsMeasured():
                    geom.SetMeasured(False)

                geom = geom.MakeValid()

                # if the geometry has more than one part, it needs to be split into multiple features
                count = geom.GetGeometryCount()
                single = False
                if count == 0 or count == 1:
                    count = 1
                    single = True

                for i in range(0, count):
                    if single:
                        g = geom
                    else:
                        g = geom.GetGeometryRef(i)
                    dst_feature = ogr.Feature(dst_layer_def)
                    dst_feature.SetGeometry(g)
                    dst_feature.SetField(self.output_id_field, self.output_id)

                    # Field Mapping
                    if self.field_map is not None:
                        metadata = {}
                        for src_field, map in self.field_map.items():
                            value = src_feature.GetField(src_field)
                            # change empty stringd to None
                            if value == '':
                                value = None
                            output = {}
                            if map == '- METADATA -':
                                metadata.update({src_field: value})
                            elif map == 'display_label':
                                # legacy support for mask display_label
                                value = str(src_feature.GetFID()) if src_field == src_fid_field_name else value
                                output.update({'display_label': value})
                            elif isinstance(map, dict):
                                # this is a value map
                                value_map = map[value]
                                for dest_field, out_value in value_map.items():
                                    output[dest_field] = out_value
                            else:
                                output = {map: value}

                            for dest_field, out_value in output.items():
                                dst_feature.SetField(dest_field, out_value)
                        # add metadata field if it is not empty
                        if metadata:
                            dst_feature.SetField('metadata', json.dumps(metadata))
                    err = dst_layer.CreateFeature(dst_feature)
                    dst_feature = None
                    if err != 0:
                        fid = src_feature.GetFID()
                        raise Exception(f'Error creating feature {fid}: {err}')
                    else:
                        self.out_feats += 1

            src_dataset = None
            dst_dataset = None

            if self.out_feats == 0:
                raise Exception("No features were imported. Check that the source and destination coordinate systems are the same and that the source and aoi mask geometries intersect.")

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
            QgsMessageLog.logMessage('Import Feature Class completed', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Feature Class Import not successful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Feature Class Import exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.import_complete.emit(result, self.in_feats, self.out_feats)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Feature Class Import was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
