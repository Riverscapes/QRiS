from .riverscapes_map_manager import RiverscapesMapManager

from ..model.project import Project, PROJECT_MACHINE_CODE
from ..model.mask import Mask, MASK_MACHINE_CODE

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

    def __init__(self) -> None:
        super().__init__()

    def build_mask_layer(self, project: Project, mask: Mask) -> QgsMapLayer:

        project_group = self.get_group_layer(project.key, PROJECT_MACHINE_CODE, project.name, None, True)
        group_layer = self.get_group_layer(project.key, MASK_MACHINE_CODE, 'Masks', project_group, True)

        feature_layer = self.create_feature_layer(project.key, group_layer, mask, 'mask_id', 'mask')

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Mask Feature ID')
        self.set_hidden(feature_layer, 'mask_id', 'Mask ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'area')

        return feature_layer
