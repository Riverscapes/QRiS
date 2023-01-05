import os
import sqlite3
import json

from qgis.PyQt.QtGui import QStandardItem, QColor
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtXml import QDomDocument

from ..QRiS.settings import CONSTANTS

from ..model.db_item import DBItem
from ..model.basemap import BASEMAP_MACHINE_CODE

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


class RiverscapesMapManager():

    def __init__(self, product_key) -> None:
        super().__init__()
        self.product_key = product_key
        self.symbology_folder = os.path.join(os.path.dirname(__file__), CONSTANTS['symbologyDir'])

    def __get_custom_property(self, project_key: str, db_item: DBItem) -> str:
        return f'{self.product_key}::{project_key}::{db_item.db_table_name}::{db_item.id}'

    def __get_machine_code_custom_property(self, project_key: str, machine_code: str) -> str:
        return f'{self.product_key}::{project_key}::{machine_code}'

    def get_db_item_layer(self, project_key: str, db_item: DBItem, layer: QgsLayerTreeNode) -> QgsLayerTreeNode:

        if layer is None:
            layer = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_custom_property(project_key, db_item)
        layer_custom_property = layer.customProperty(self.product_key)
        if isinstance(layer_custom_property, str) and layer_custom_property == target_custom_property:
            # Ensure it has the latest name (in case this method is called after an edit)
            layer.setName(db_item.name)
            return layer

        if isinstance(layer, QgsLayerTreeGroup):
            for child in layer.children():
                result = self.get_db_item_layer(project_key, db_item, child)
                if isinstance(result, QgsLayerTreeNode):
                    return result

        return None

    # method to get a layer based on its machine code custom property
    def get_machine_code_layer(self, project_key: str, machine_code: str, layer: QgsLayerTreeNode) -> QgsLayerTreeNode:

        if layer is None:
            layer = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_machine_code_custom_property(project_key, machine_code)
        layer_custom_property = layer.customProperty(self.product_key)
        if isinstance(layer_custom_property, str) and layer_custom_property == target_custom_property:
            return layer

        if isinstance(layer, QgsLayerTreeGroup):
            for child in layer.children():
                result = self.get_machine_code_layer(project_key, machine_code, child)
                if isinstance(result, QgsLayerTreeNode):
                    return result

        return None

    def get_group_layer(self, project_key: str, machine_code, group_label, parent: QgsLayerTreeGroup = None, add_missing: bool = False) -> QgsLayerTreeGroup:
        """
        Finds a group layer directly underneath "parent" with the specified
        machine code as the custom property. No string matching with group
        label is performed.

        When add_missing is True, the group will be created if it can't be found.
        """

        if parent is None:
            parent = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_machine_code_custom_property(project_key, machine_code)

        for child_layer in parent.children():
            custom_property = child_layer.customProperty(self.product_key)
            if isinstance(custom_property, str) and custom_property == target_custom_property:
                return child_layer

        if add_missing:
            # Find the basemaps group layer. If it is already in the map then
            # insert the new group layer ABOVE it rather than just add it (which
            # will cause it to get added below the basemaps).
            basemap_group_index = self.get_group_layer(project_key, BASEMAP_MACHINE_CODE, 'Basemaps', parent, False)

            if basemap_group_index is None:
                # No basemaps under this parent. Add the new group. It will get added last.
                group_layer = parent.addGroup(group_label)
            else:
                # Basemap group node exists. Add the new group as penultimate group.
                group_layer = parent.insertGroup(len(parent.children()) - 1, group_label)

            group_layer.setCustomProperty(self.product_key, target_custom_property)
            return group_layer

        return None

    def remove_empty_groups(self, group_node: QgsLayerTreeGroup) -> None:

        parent_node = group_node.parent()
        if parent_node is None:
            return

        if len(group_node.children()) < 1:
            parent_node.removeChildNode(group_node)

        if isinstance(parent_node, QgsLayerTreeGroup):
            self.remove_empty_groups(parent_node)

    def remove_db_item_layer(self, project_key: str, db_item: DBItem) -> None:

        layer = self.get_db_item_layer(project_key, db_item, None)
        if layer is not None:
            parent_group = layer.parent()
            parent_group.removeChildNode(layer)
            self.remove_empty_groups(parent_group)

    def create_db_item_feature_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, fc_path: str, db_item: DBItem, id_field: str, symbology_key: str) -> QgsVectorLayer:
        """
        Creates a new feature layer for the specified DBItem and adds it to the map.
        args:
            project_key: The project key
                db_item: The DBItem to create a layer for
                symbology: The symbology to apply to the layer. File name only. No folder or extension."""

        layer = self.get_db_item_layer(project_key, db_item, None)
        if layer is not None:
            return layer

        # Create a layer from the table
        layer = QgsVectorLayer(fc_path, db_item.name, 'ogr')
        QgsProject.instance().addMapLayer(layer, False)

        # Apply symbology
        qml = os.path.join(self.symbology_folder, 'symbology', f'{symbology_key}.qml')
        layer.loadNamedStyle(qml)

        # Filter to just the features for this item
        layer.setSubsetString(f'{id_field} = ' + str(db_item.id))

        # Set a parent assessment variable
        QgsExpressionContextUtils.setLayerVariable(layer, id_field, db_item.id)
        # Set the default value from the variable
        mask_field_index = layer.fields().indexFromName(id_field)
        layer.setDefaultValueDefinition(mask_field_index, QgsDefaultValue(f'@{id_field}'))

        # Finally add the new layer here
        QgsProject.instance().addMapLayer(layer, False)
        tree_layer_node = parent_group.addLayer(layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_custom_property(project_key, db_item))

        return layer

    def create_machine_code_feature_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, fc_path: str, machine_code: str, display_label: str, symbology_key: str) -> QgsVectorLayer:
        """
        Creates a new feature layer for the specified machine code and adds it to the map.
        args:
            project_key: The project key
                db_item: The DBItem to create a layer for
                symbology: The symbology to apply to the layer. File name only. No folder or extension."""

        layer = self.get_machine_code_layer(project_key, machine_code, None)
        if layer is not None:
            return layer

        # Create a layer from the table
        layer = QgsVectorLayer(fc_path, display_label, 'ogr')
        QgsProject.instance().addMapLayer(layer, False)

        # Apply symbology
        qml = os.path.join(self.symbology_folder, 'symbology', f'{symbology_key}.qml')
        layer.loadNamedStyle(qml)

        # Finally add the new layer here
        tree_layer_node = parent_group.addLayer(layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_machine_code_custom_property(project_key, machine_code))

        return layer

    def set_multiline(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        widget_setup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True, 'UseHtml': False})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)
        feature_layer.setFieldAlias(field_index, field_alias)
        form_config = feature_layer.editFormConfig()
        form_config.setLabelOnTop(field_index, True)
        feature_layer.setEditFormConfig(form_config)

    def set_hidden(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
        """Sets a field to hidden, read only, and also sets an alias just in case. Often used on fid, project_id, and event_id"""
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        form_config = feature_layer.editFormConfig()
        form_config.setReadOnly(field_index, True)
        feature_layer.setEditFormConfig(form_config)
        feature_layer.setFieldAlias(field_index, field_alias)
        widget_setup = QgsEditorWidgetSetup('Hidden', {})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)

    def set_alias(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str, parent_container=None, display_index=None) -> None:
        """Just provides an alias to the field for display"""
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        feature_layer.setFieldAlias(field_index, field_alias)
        if parent_container is not None and display_index is not None:
            form_config = feature_layer.editFormConfig()
            editor_field = QgsAttributeEditorField(field_name, display_index, parent_container)
            parent_container.addChildElement(editor_field)
            feature_layer.setEditFormConfig(form_config)

    # ----- CREATING VIRTUAL FIELDS --------

    def set_virtual_dimension(self, feature_layer: QgsVectorLayer, dimension: str) -> None:
        """dimension should be 'area' or 'length'
        sets a virtual length field named vrt_length
        aliases the field as Length (m)
        sets the widget type to text
        sets default value to the dimension expression"""

        field_name = 'vrt_' + dimension
        field_alias = dimension.capitalize() + ' (m)'
        field_expression = 'round(${}, 0)'.format(dimension)
        virtual_field = QgsField(field_name, QVariant.Int)
        feature_layer.addExpressionField(field_expression, virtual_field)
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        feature_layer.setFieldAlias(field_index, field_alias)
        feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(field_expression))
        widget_setup = QgsEditorWidgetSetup('TextEdit', {})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)

    def set_created_datetime(self, feature_layer: QgsVectorLayer) -> None:
        """Will set a date time created field to a default value of now() and also set it to read only"""

        fields = feature_layer.fields()
        field_index = fields.indexFromName('created')
        feature_layer.setFieldAlias(field_index, 'Created')
        feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("now()"))
        form_config = feature_layer.editFormConfig()
        form_config.setReadOnly(field_index, True)
        feature_layer.setEditFormConfig(form_config)

    def set_label(self, feature_layer: QgsVectorLayer, label_field: str) -> None:
        """Sets the label field for the layer
        Labeling learned here:
        https://gis.stackexchange.com/questions/273266/reading-and-setting-label-settings-in-pyqgis/273268#273268
        """
        layer_settings = QgsPalLayerSettings()
        layer_settings.fieldName = label_field
        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        feature_layer.setLabelsEnabled(True)
        feature_layer.setLabeling(layer_settings)
