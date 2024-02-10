import os
import json
from typing import List

from osgeo import ogr, osr

from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal

from ..gp.feature_class_functions import layer_path_parser

MESSAGE_CATEGORY = 'QRiS_ImportFeatureClassTask'

# create a data class to store 'src_field', 'dest_field', and optional 'map' values
class ImportFieldMap:
    def __init__(self, src_field: str, dest_field: str=None, map: dict = None, parent=None):
        self.src_field = src_field
        self.dest_field = dest_field
        self.map = map
        self.parent = parent

class ImportFeatureClass(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    import_complete = pyqtSignal(bool, int, int, int)

    def __init__(self, source_path: str, dest_path: str, attributes:dict= None, field_map: List[ImportFieldMap] = None, clip_mask_id=None, attribute_filter: str = None, proj_gpkg=None):
        super().__init__(f'Import Feature Class Task', QgsTask.CanCancel)

        self.source_path = source_path
        self.clip_mask_id = clip_mask_id
        self.output_path = dest_path
        self.field_map = field_map
        self.attributes = attributes
        self.attribute_filter = attribute_filter
        self.in_feats = 0
        self.out_feats = 0
        self.skipped_feats = 0
        self.proj_gpkg = proj_gpkg

    def run(self):

        self.setProgress(0)

        copy_fields = False
        src_dataset = None
        dst_dataset = None
        result = True

        try:
            src_path, _src_layer_name, src_layer_id = layer_path_parser(self.source_path)
            src_dataset: ogr.DataSource = ogr.Open(src_path)
            src_layer: ogr.Layer = src_dataset.GetLayer(src_layer_id)
            src_srs = src_layer.GetSpatialRef()
            if self.attribute_filter is not None:
                src_layer.SetAttributeFilter(self.attribute_filter)
            src_fid_field_name = src_layer.GetFIDColumn()
            self.in_feats = src_layer.GetFeatureCount()

            dst_path, dst_layer_name, _dst_layer_id = layer_path_parser(self.output_path)

            base_path = os.path.dirname(dst_path)
            if not os.path.exists(base_path):
                os.makedirs(base_path)

            gpkg_driver: ogr.Driver = ogr.GetDriverByName('GPKG')
            if not os.path.exists(dst_path):
                dst_dataset: ogr.DataSource = gpkg_driver.CreateDataSource(dst_path)
            else:
                dst_dataset = gpkg_driver.Open(dst_path, 1)

            dst_layer: ogr.Layer = dst_dataset.GetLayerByName(dst_layer_name)
            if dst_layer is None:
                copy_fields = True
                # create the layer based on the source layer
                dst_layer = dst_dataset.CreateLayer(dst_layer_name, src_srs, src_layer.GetGeomType())
                # add the fields from the source layer
                src_layer_def: ogr.FeatureDefn = src_layer.GetLayerDefn()
                for i in range(src_layer_def.GetFieldCount()):
                    src_field = src_layer_def.GetFieldDefn(i)
                    dst_layer.CreateField(src_field)

            dst_srs = dst_layer.GetSpatialRef()
            dst_layer_def = dst_layer.GetLayerDefn()
            dst_fid_column = dst_layer.GetFIDColumn()

            clip_geom = None
            if self.clip_mask_id is not None:
                if self.proj_gpkg is not None:
                    mask_dataset = ogr.Open(self.proj_gpkg)
                else:
                    mask_dataset = dst_dataset
                clip_layer: ogr.Layer = mask_dataset.GetLayer('aoi_features')
                clip_layer.SetAttributeFilter(f'mask_id = {self.clip_mask_id}')
                # Gather all of the geoms and merge into a multipart geometry
                clip_geom = ogr.Geometry(ogr.wkbMultiPolygon)
                for clip_feat in clip_layer:
                    clip_geom.AddGeometry(clip_feat.GetGeometryRef())
                # clip_geom = clip_geom.UnionCascaded()
                clip_transform = osr.CoordinateTransformation(clip_layer.GetSpatialRef(), src_srs)
                clip_geom.Transform(clip_transform)

            transform = osr.CoordinateTransformation(src_srs, dst_srs)

            self.out_feats = 0
            src_feature: ogr.Feature = None
            for src_feature in src_layer:

                geom: ogr.Geometry = src_feature.GetGeometryRef()


                if geom is None:
                    self.skipped_feats += 1
                    continue

                if geom.IsEmpty():
                    self.skipped_feats += 1
                    continue

                if not geom.IsValid():
                    geom = geom.MakeValid()
                    if not geom.IsValid():
                        continue

                if clip_geom is not None:
                    geom = clip_geom.Intersection(geom)
                    if geom.IsEmpty():
                        continue

                geom.Transform(transform)
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
                        g.MakeValid()
                        if not g.IsValid():
                            continue
                    dst_feature = ogr.Feature(dst_layer_def)
                    dst_feature.SetGeometry(g)
                    if self.attributes is not None:
                        for field_name, field_value in self.attributes.items():
                            dst_feature.SetField(field_name, field_value)

                    # Field Mapping
                    if self.field_map is not None:
                        metadata = {}
                        field_map: ImportFieldMap = None
                        for field_map in self.field_map:
                            value = src_feature.GetField(field_map.src_field)
                            # change empty stringd to None
                            if value == '':
                                value = None
                            if field_map.dest_field == 'display_label':
                                value = str(src_feature.GetFID()) if field_map.src_field == src_fid_field_name else value
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
                            dst_feature.SetField('metadata', json.dumps(metadata))

                    if copy_fields is True:
                        # copy the field values from the source layer
                        for i in range(src_feature.GetFieldCount()):
                            src_field: ogr.FieldDefn = src_feature.GetFieldDefnRef(i)
                            if src_field.GetNameRef() != dst_fid_column:
                                dst_feature.SetField(src_field.GetNameRef(), src_feature.GetField(i))

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

        except Exception as ex:
            self.exception = ex
            result = False

        finally:
            if src_dataset is not None:
                src_dataset = None
            if dst_dataset is not None:
                dst_dataset = None
            return result

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

        self.import_complete.emit(result, self.in_feats, self.out_feats, self.skipped_feats)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Feature Class Import was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
