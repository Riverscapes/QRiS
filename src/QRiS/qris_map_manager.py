import os

from .riverscapes_map_manager import RiverscapesMapManager

from ..model.project import Project, PROJECT_MACHINE_CODE
from ..model.mask import Mask, MASK_MACHINE_CODE
from ..model.stream_gage import StreamGage, STREAM_GAGE_MACHINE_CODE
from ..model.scratch_vector import ScratchVector, SCRATCH_VECTOR_MACHINE_CODE
from ..model.pour_point import PourPoint
from ..model.basemap import Raster, BASEMAP_MACHINE_CODE

from qgis.core import (
    QgsField,
    QgsLayerTreeGroup,
    QgsLayerTreeNode,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsLayerTree,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsMapLayer,
    QgsFeatureRequest,
    QgsSymbol,
    QgsRendererCategory,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsSimpleFillSymbolLayer,
    QgsCategorizedSymbolRenderer,
    QgsProject,
    QgsExpressionContextUtils,
    QgsFieldConstraints,
    qgsfunction,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsRasterBandStats,
    QgsAttributeEditorContainer,
    QgsAttributeEditorElement,
    QgsReadWriteContext,
    QgsEditFormConfig,
    QgsAttributeEditorField,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsAction,
    QgsAttributeEditorAction
)


class QRisMapManager(RiverscapesMapManager):

    def __init__(self, project: Project) -> None:
        super().__init__('QRiS')
        self.project = project

    def build_mask_layer(self, mask: Mask) -> QgsMapLayer:

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, MASK_MACHINE_CODE, 'Masks', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, mask, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = self.project.project_file + '|layername=' + 'mask_features'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, mask, 'mask_id', 'mask')

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Mask Feature ID')
        self.set_hidden(feature_layer, 'mask_id', 'Mask ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'area')

        return feature_layer

    def get_stream_gage_layer(self) -> QgsMapLayer:
        """Returns the stream gage layer if it exists. Otherwise returns None"""

        return self.get_machine_code_layer(self.project.map_guid, STREAM_GAGE_MACHINE_CODE, None)

    def build_stream_gage_layer(self, project: Project) -> QgsMapLayer:

        feature_layer = self.get_stream_gage_layer()
        if feature_layer is not None:
            return feature_layer

        project_group = self.get_group_layer(project.map_guid, PROJECT_MACHINE_CODE, project.name, None, True)

        fc_path = project.project_file + '|layername=' + 'stream_gages'

        self.create_machine_code_feature_layer(project.map_guid, project_group, fc_path, STREAM_GAGE_MACHINE_CODE, 'Stream Gages', 'stream_gages')

        # Apply labels
        self.set_label(feature_layer, 'site_code')

        return feature_layer

    def build_scratch_vector(self, vector: ScratchVector):

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(SCRATCH_VECTOR_MACHINE_CODE, 'Scratch Vectors', project_group, True)
        fc_path: str = vector.gpkg_path + '|layername=' + vector.fc_name
        layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, vector, 'vector_id', 'vector')

        return layer

    # def build_pour_point_map_layer(self, pour_point: PourPoint):

    #     if check_for_existing_layer(project, pour_point) is not None:
    #         return

    #     project_group = get_project_group(project)
    #     context_group_layer = get_group_layer(CONTEXT_NODE_TAG, 'Context', project_group, True)
    #     pour_point_group_layer = get_group_layer(pour_point, pour_point.name, context_group_layer, True)

    #     # Create a layer from the pour point
    #     point_feature_path = project.project_file + '|layername=' + 'pour_points'
    #     point_feature_layer = QgsVectorLayer(point_feature_path, 'Pour Point', 'ogr')
    #     point_feature_layer.setSubsetString('fid = ' + str(pour_point.id))
    #     QgsProject.instance().addMapLayer(point_feature_layer, False)
    #     pour_point_group_layer.addLayer(point_feature_layer)
    #     qml = os.path.join(symbology_path, 'symbology', 'pour_point.qml')
    #     point_feature_layer.loadNamedStyle(qml)

    #     catchment_feature_path = project.project_file + '|layername=' + 'catchments'
    #     catchment_feature_layer = QgsVectorLayer(catchment_feature_path, 'Catchment', 'ogr')
    #     catchment_feature_layer.setSubsetString('pour_point_id = ' + str(pour_point.id))
    #     QgsExpressionContextUtils.setLayerVariable(catchment_feature_layer, 'pour_point_id', pour_point.id)
    #     qml = os.path.join(symbology_path, 'symbology', 'catchment.qml')
    #     catchment_feature_layer.loadNamedStyle(qml)

    #     QgsProject.instance().addMapLayer(catchment_feature_layer, False)
    #     pour_point_group_layer.addLayer(catchment_feature_layer)

    #     return point_feature_layer, catchment_feature_layer

    def build_basemap_layer(self, basemap: Raster) -> QgsMapLayer:

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, BASEMAP_MACHINE_CODE, 'Basemaps', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, basemap, None)  # TODO search entire toc or just project??
        if existing_layer is not None:
            return existing_layer

        raster_path = os.path.join(os.path.dirname(self.project.project_file), basemap.path)
        raster_layer = self.create_db_item_raster_layer(self.project.map_guid, group_layer, raster_path, basemap)

        return raster_layer
