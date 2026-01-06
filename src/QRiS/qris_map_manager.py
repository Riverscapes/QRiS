import os
import json
from textwrap import dedent

from .riverscapes_map_manager import RiverscapesMapManager

from ..model.project import Project, PROJECT_MACHINE_CODE
from ..model.sample_frame import SampleFrame, SAMPLE_FRAME_MACHINE_CODE, AOI_MACHINE_CODE, VALLEY_BOTTOM_MACHINE_CODE
from ..model.stream_gage import StreamGage, STREAM_GAGE_MACHINE_CODE
from ..model.scratch_vector import ScratchVector, SCRATCH_VECTOR_MACHINE_CODE
from ..model.pour_point import PourPoint, CATCHMENTS_MACHINE_CODE
from ..model.raster import Raster, BASEMAP_MACHINE_CODE, SURFACE_MACHINE_CODE, CONTEXT_MACHINE_CODE, RASTER_SLIDER_MACHINE_CODE, get_raster_symbology
from ..model.event import EVENT_MACHINE_CODE, DESIGN_EVENT_TYPE_ID, DESIGN_MACHINE_CODE, AS_BUILT_MACHINE_CODE, AS_BUILT_EVENT_TYPE_ID, Event
from ..model.event_layer import EventLayer
from ..model.profile import Profile
from ..model.cross_sections import CrossSections

from ..lib.climate_engine import CLIMATE_ENGINE_MACHINE_CODE

from .path_utilities import parse_posix_path

from qgis.utils import iface
from qgis.core import (
    Qgis,
    QgsVectorLayer,
    QgsMapLayer,
    QgsProject,
    QgsExpressionContextUtils,
    qgsfunction,
    QgsAttributeEditorContainer,
    QgsDefaultValue,
    QgsAction,
    QgsAttributeEditorAction,
    QgsMessageLog,
    QgsCoordinateReferenceSystem
)



class QRisMapManager(RiverscapesMapManager):

    def __init__(self, project: Project) -> None:
        super().__init__('QRiS')
        self.project: Project = project
        # add the project folder to the front of symbology_folders
        self.symbology_folders.insert(0, os.path.dirname(self.project.project_file))

        self.layer_order = [
            CrossSections.CROSS_SECTIONS_MACHINE_CODE,
            Profile.PROFILE_MACHINE_CODE,
            AOI_MACHINE_CODE,
            SAMPLE_FRAME_MACHINE_CODE,
            VALLEY_BOTTOM_MACHINE_CODE,
            f'{EVENT_MACHINE_CODE}_ROOT',
            f'{DESIGN_MACHINE_CODE}_ROOT',
            STREAM_GAGE_MACHINE_CODE,
            f'{RASTER_SLIDER_MACHINE_CODE}_ROOT',
            CONTEXT_MACHINE_CODE,
            SURFACE_MACHINE_CODE,
            CLIMATE_ENGINE_MACHINE_CODE,
            'QRiS Base Maps',
            BASEMAP_MACHINE_CODE]

    def build_aoi_layer(self, aoi: SampleFrame) -> QgsMapLayer:

        group_layer_name = 'AOIs'
        mask_machine_code = AOI_MACHINE_CODE
        symbology = 'mask'  # TODO do aois need a different mask type? make the reference here...
        layer_name = 'sample_frame_features'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, mask_machine_code, group_layer_name, project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, aoi, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername={layer_name}'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, aoi, 'sample_frame_id', symbology)

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'AOI Feature ID')
        self.set_hidden(feature_layer, 'sample_frame_id', 'AOI ID')
        self.set_alias(feature_layer, 'display_label', 'Display Label')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_hidden(feature_layer, 'flow_path', 'Flow Path', hide_in_attribute_table=True)
        self.set_hidden(feature_layer, 'flows_into', 'Flows Into', hide_in_attribute_table=True)
        self.set_virtual_dimension(feature_layer, 'area')
        self.set_metadata_virtual_fields(feature_layer)

        return feature_layer
    
    def build_sample_frame_layer(self, sample_frame: SampleFrame) -> QgsMapLayer:

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, SAMPLE_FRAME_MACHINE_CODE, 'Sample Frames', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, sample_frame, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername=sample_frame_features'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, sample_frame, 'sample_frame_id', 'sampling_frames')

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Sample Frame Feature ID')
        self.set_hidden(feature_layer, 'sample_frame_id', 'Sample Frame ID')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'area')
        self.set_metadata_virtual_fields(feature_layer)

        return feature_layer


    def build_profile_layer(self, profile: Profile) -> QgsMapLayer:

        if profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE:
            symbology = 'centerlines_saved'
            layer_name = 'profile_centerlines'
        else:
            symbology = 'profile'
            layer_name = 'profile_features'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, Profile.PROFILE_MACHINE_CODE, 'Profiles', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, profile, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername={layer_name}'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, profile, 'profile_id', symbology)

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Profile Feature ID')
        self.set_hidden(feature_layer, 'profile_id', 'Profile ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'length')

        return feature_layer

    def build_cross_section_layer(self, cross_sections: CrossSections) -> QgsMapLayer:

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, CrossSections.CROSS_SECTIONS_MACHINE_CODE, 'Cross Sections', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, cross_sections, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername=cross_section_features'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, cross_sections, 'cross_section_id', 'cross_sections')

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Cross Section Feature ID')
        self.set_hidden(feature_layer, 'cross_section_id', 'Cross Sections ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'length')
        self.set_metadata_virtual_fields(feature_layer)

        return feature_layer
    
    def build_valley_bottom_layer(self, valley_bottom: SampleFrame) -> QgsMapLayer:
            
            project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
            group_layer = self.get_group_layer(self.project.map_guid, VALLEY_BOTTOM_MACHINE_CODE, 'Valley Bottoms', project_group, True)
    
            existing_layer = self.get_db_item_layer(self.project.map_guid, valley_bottom, group_layer)
            if existing_layer is not None:
                return existing_layer
    
            fc_path = f'{self.project.project_file}|layername=sample_frame_features'
            feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, valley_bottom, 'sample_frame_id', 'valley_bottom')
    
            # setup fields
            self.set_hidden(feature_layer, 'fid', 'VB Feature ID')
            self.set_hidden(feature_layer, 'sample_frame_id', 'Valley Bottom ID')
            self.set_alias(feature_layer, 'display_label', 'Display Label')
            self.set_hidden(feature_layer, 'flow_path', 'Flow Path', hide_in_attribute_table=True)
            self.set_hidden(feature_layer, 'flows_into', 'Flows Into', hide_in_attribute_table=True)
            self.set_multiline(feature_layer, 'description', 'Description')
            self.set_hidden(feature_layer, 'metadata', 'Metadata')
            self.set_virtual_dimension(feature_layer, 'area')
            self.set_metadata_virtual_fields(feature_layer)
    
            return feature_layer

    def build_stream_gage_layer(self) -> QgsMapLayer:

        existing_layer = self.get_machine_code_layer(self.project.map_guid, STREAM_GAGE_MACHINE_CODE, None)
        if existing_layer is not None:
            return existing_layer

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        # TODO Do stream guages need a Group layer?
        fc_path = self.project.project_file + '|layername=' + 'stream_gages'
        feature_layer = self.create_machine_code_feature_layer(self.project.map_guid, project_group, fc_path, STREAM_GAGE_MACHINE_CODE, 'Stream Gages', 'stream_gages')

        # Apply labels
        self.set_label(feature_layer, 'site_code')

        return feature_layer

    def build_scratch_vector(self, vector: ScratchVector):

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, CONTEXT_MACHINE_CODE, 'Context', project_group, True)
        fc_path: str = vector.gpkg_path + '|layername=' + vector.fc_name
        symbology = None
        if vector.metadata is not None:
            system_metadata: dict = vector.metadata.get('system', None)
            if system_metadata is not None:
                symbology = system_metadata.get('symbology', None)
        existing_layer = self.get_db_item_layer(self.project.map_guid, vector, None)
        if existing_layer is not None:
            return
        layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, vector, None, symbology)

        return layer

    def build_pour_point_map_layer(self, pour_point: PourPoint):

        existing_layer = self.get_db_item_layer(self.project.map_guid, pour_point, None)
        if existing_layer is not None:
            return

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        context_group_layer = self.get_group_layer(self.project.map_guid, CONTEXT_MACHINE_CODE, 'Context', project_group, True)
        catchment_deliniation_group_layer = self.get_group_layer(self.project.map_guid, CATCHMENTS_MACHINE_CODE, 'Catchment Delineations', context_group_layer, True)
        pour_point_group_layer = self.get_group_layer(self.project.map_guid, pour_point, pour_point.name, catchment_deliniation_group_layer, True)

        # Create a layer from the pour point
        point_fc_path = self.project.project_file + '|layername=' + 'pour_points'
        # point_feature_layer = self.create_db_item_feature_layer(self.project.map_guid, pour_point_group_layer, point_fc_path, pour_point, 'fid', 'pour_point')
        point_feature_layer = QgsVectorLayer(point_fc_path, 'Pour Point', 'ogr')
        if point_feature_layer and not point_feature_layer.crs().isValid():
            point_feature_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        point_feature_layer.setSubsetString('fid = ' + str(pour_point.id))
        QgsProject.instance().addMapLayer(point_feature_layer, False)
        pour_point_layer_node = pour_point_group_layer.addLayer(point_feature_layer)
        qml = self.get_symbology_qml("pour_point") 
        point_feature_layer.loadNamedStyle(qml)
        point_machine_code = f'pour_point_{pour_point.id}'
        pour_point_layer_node.setCustomProperty(self.product_key, f'{self.product_key}::{self.project.map_guid}::{point_machine_code}')

        catchment_fc_path = self.project.project_file + '|layername=' + 'catchments'
        # catchment_feature_layer = self.create_db_item_feature_layer(self.project.map_guid, pour_point_group_layer, catchment_fc_path, pour_point, 'fid', 'catchment')
        catchment_feature_layer = QgsVectorLayer(catchment_fc_path, 'Catchment', 'ogr')
        if catchment_feature_layer and not catchment_feature_layer.crs().isValid():
            catchment_feature_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        catchment_feature_layer.setSubsetString('pour_point_id = ' + str(pour_point.id))
        QgsExpressionContextUtils.setLayerVariable(catchment_feature_layer, 'pour_point_id', pour_point.id)
        qml = self.get_symbology_qml('catchment')
        catchment_feature_layer.loadNamedStyle(qml)
        QgsProject.instance().addMapLayer(catchment_feature_layer, False)
        catchment_layer_node = pour_point_group_layer.addLayer(catchment_feature_layer)
        catchment_machine_code = f'catchment_{pour_point.id}'
        catchment_layer_node.setCustomProperty(self.product_key, f'{self.product_key}::{self.project.map_guid}::{catchment_machine_code}')


        return point_feature_layer, catchment_feature_layer

    def remove_pour_point_layers(self, pour_point: PourPoint) -> None:

        pour_point_machine_code = f'pour_point_{pour_point.id}'
        pour_point_layer = self.get_machine_code_layer(self.project.map_guid, pour_point_machine_code, None)
        if pour_point_layer is not None:
            parent_group = pour_point_layer.parent()
            parent_group.removeChildNode(pour_point_layer)
            self.remove_empty_groups(parent_group)

        catchment_machine_code = f'catchment_{pour_point.id}'
        catchment_layer = self.get_machine_code_layer(self.project.map_guid, catchment_machine_code, None)
        if catchment_layer is not None:
            parent_group = catchment_layer.parent()
            parent_group.removeChildNode(catchment_layer)
            self.remove_empty_groups(parent_group)


    def build_raster_layer(self, raster: Raster) -> QgsMapLayer:

        # check if raster file exists on disk
        path = parse_posix_path(os.path.join(os.path.dirname(self.project.project_file), raster.path))
        if not os.path.exists(path):
            # Warn user that the raster file is missing
            iface.messageBar().pushMessage('Missing QRiS Raster File', f'The raster file {path} referenced in the QRiS project is missing.', level=Qgis.Warning)
            return None
        
        if raster.is_context is False:
            raster_machine_code = SURFACE_MACHINE_CODE
            group_layer_name = 'Surfaces'
        else:
            raster_machine_code = CONTEXT_MACHINE_CODE
            group_layer_name = 'Context'
        # else:
        #     raster_machine_code = BASEMAP_MACHINE_CODE
        #     group_layer_name = 'Basemaps'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, raster_machine_code, group_layer_name, project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, raster, None)  # TODO search entire toc or just project??
        if existing_layer is not None:
            return existing_layer

        raster_path = parse_posix_path(os.path.join(os.path.dirname(self.project.project_file), raster.path))
        symbology = None
        symbology_key = get_raster_symbology(self.project.project_file, raster.raster_type_id)
        if symbology_key is None:
            # look for symbology in system metadata
            if raster.metadata is not None:
                system_metadata: dict = raster.metadata.get('system', None)
                if system_metadata is not None:
                    symbology = system_metadata.get('symbology', None)
        if symbology_key is not None:
            symbology = self.get_symbology_qml(symbology_key)
        raster_layer = self.create_db_item_raster_layer(self.project.map_guid, group_layer, raster_path, raster, symbology)

        return raster_layer

    def build_raster_slider_layer(self, raster: Raster) -> QgsMapLayer:

        # Add raster normally as a contextual layer
        self.build_raster_layer(raster)

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, f'{RASTER_SLIDER_MACHINE_CODE}_ROOT', 'Raster Slider', project_group, True)

        # Remove any existing raster layer in this group
        group_layer.removeAllChildren()

        raster_path = parse_posix_path(os.path.join(os.path.dirname(self.project.project_file), raster.path))
        raster_layer = self.create_machine_code_raster_layer(self.project.map_guid, group_layer, raster_path, raster, RASTER_SLIDER_MACHINE_CODE)

        return raster_layer

    def build_event_single_layer(self, event: Event, event_layer: EventLayer) -> None:
        """
        Add a single layer for an event
        """
        # if lookup table then forget about it
        if event_layer.layer.is_lookup:
            return

        machine_code = EVENT_MACHINE_CODE
        group_name = 'Data Capture Events'
        if event.event_type.id == DESIGN_EVENT_TYPE_ID:
            machine_code = DESIGN_MACHINE_CODE
            group_name = 'Designs'
        if event.event_type.id == AS_BUILT_EVENT_TYPE_ID:
            machine_code = AS_BUILT_MACHINE_CODE
            group_name = 'As-Builts'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        events_group_layer = self.get_group_layer(self.project.map_guid, f'{machine_code}_ROOT', group_name, project_group, True)
        event_group_layer = self.get_group_layer(self.project.map_guid, f'{machine_code}_{event.id}', event.name, events_group_layer, True)
        
        group_layer = event_group_layer
        if event_layer.layer.hierarchy is not None:
            # need to add group layers for each hierarchy level
            for hierarchy_level in event_layer.layer.hierarchy:
                group_layer = self.get_group_layer(self.project.map_guid, f'{machine_code}_{event.id}_{hierarchy_level}', hierarchy_level, group_layer, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, event_layer, group_layer)
        if existing_layer is not None:
            return

        if event_layer.layer.geom_type == 'Point':
            fc_name = 'dce_points'
        elif event_layer.layer.geom_type == 'Linestring':
            fc_name = 'dce_lines'
        elif event_layer.layer.geom_type == 'Polygon':
            fc_name = 'dce_polygons'
        else:
            raise Exception('Unknown geom type')

        fc_path = f'{self.project.project_file}|layername={fc_name}|subset=event_id = {event.id} AND event_layer_id = {event_layer.layer.id}'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, event_layer, None, event_layer.layer.qml)
        if feature_layer and not feature_layer.crs().isValid():
            feature_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        
        for id_field, id_value in {'event_id': event.id, 'event_layer_id': event_layer.layer.id}.items():
            QgsExpressionContextUtils.setLayerVariable(feature_layer, id_field, id_value)
            # Set the default value from the variable
            field_index = feature_layer.fields().indexFromName(id_field)
            feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(f'@{id_field}'))

        self.set_hidden(feature_layer, 'fid', 'Feature ID')
        self.set_hidden(feature_layer, 'event_layer_id', 'Layer ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.metadata_field(feature_layer, event_layer, 'metadata')

        # add length field for line layers
        if event_layer.layer.geom_type == 'Linestring':
            self.set_virtual_dimension(feature_layer, 'length')

        # add area field for polygon layers
        if event_layer.layer.geom_type == 'Polygon':
            self.set_virtual_dimension(feature_layer, 'area')

    def metadata_field(self, feature_layer: QgsVectorLayer, event_layer: EventLayer, field_name: str) -> None:
        config: dict = event_layer.layer.metadata
        if 'fields' not in config:
            config['fields'] = []
            
        # add 'values' to config from self.lookups if the field has 'lookup' as an attribute
        fields: list = config.get('fields', [])
        field: dict
        for ix, field in enumerate(fields):
            if 'lookup' in field:
                if field['lookup'] in self.project.lookup_values:
                    config['fields'][ix]['values'] = self.project.lookup_values[field['lookup']]
                else:
                    config['fields'][ix]['values'] = []
        # add a notes field if it doesn't exist
        if 'notes' not in [field['id'] for field in fields]:
            config['fields'].append({'id': 'notes', 'type': 'long_text', 'label': 'Notes'})

        # build virtual metadata fields for attribute table
        default_photo_path = os.path.join(os.path.dirname(self.project.project_file), 'photos', f'dce_{str(event_layer.event_id).zfill(3)}').replace('\\', '/')
        self.set_metadata_virtual_fields(feature_layer, config, default_photo_path)

        # prepare the metadata attribute editor widget
        self.set_metadata_attribute_editor(feature_layer, 'metadata', 'Metadata', config)
        column_index = feature_layer.fields().indexOf('metadata')
        if column_index != -1:
            layer_attr_table_config = feature_layer.attributeTableConfig()
            layer_attr_table_config.setColumnHidden(column_index, True)
            feature_layer.setAttributeTableConfig(layer_attr_table_config)
        else:
            QgsMessageLog.logMessage(
                f"'metadata' field not found in layer '{feature_layer.name()}'. Skipping column hide.",
                "QRiS", Qgis.Warning
            )

    def add_brat_cis(self, feature_layer: QgsVectorLayer) -> None:
        # first read and set the lookup tables
        self.set_table_as_layer_variable(feature_layer, self.project.project_file, "lkp_brat_vegetation_cis")
        self.set_table_as_layer_variable(feature_layer, self.project.project_file, "lkp_brat_combined_cis")

        # attribute form containers: https://gis.stackexchange.com/questions/310287/qgis-editform-layout-settings-in-python
        editFormConfig = feature_layer.editFormConfig()
        editFormConfig.setLayout(1)
        rootContainer = editFormConfig.invisibleRootContainer()
        rootContainer.clear()

        # FID and Event ID will not show up on the form since we cleared them from the root container, but need to set alias for attribute table.
        self.set_hidden(feature_layer, 'fid', 'Brat Cis ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')

        # Info Group Box
        info_container = QgsAttributeEditorContainer('BRAT Observation Event', rootContainer)
        self.set_alias(feature_layer, 'reach_id', 'Reach ID', info_container, 0)
        self.set_alias(feature_layer, 'observation_date', 'Observation Date', info_container, 1)
        self.set_alias(feature_layer, 'reach_length', 'Reach Length (m)', info_container, 2)
        self.set_alias(feature_layer, 'notes', 'Notes', info_container, 3)
        self.set_alias(feature_layer, 'observer_name', 'Observer Name', info_container, 4)
        editFormConfig.addTab(info_container)

        # Add buffer button
        self.add_buffer_action(feature_layer, rootContainer)

        # Vegetation Evidence Group Box
        veg_container = QgsAttributeEditorContainer('Vegetation Evidence CIS', rootContainer)
        self.set_value_map(feature_layer, 'streamside_veg_id', self.project.project_file, 'lkp_brat_vegetation_types', 'Streamside Vegetation', parent_container=veg_container, display_index=0)
        self.set_value_map(feature_layer, 'riparian_veg_id', self.project.project_file, 'lkp_brat_vegetation_types', 'Riparian Vegetation', parent_container=veg_container, display_index=1)
        veg_expression = 'get_veg_dam_density(streamside_veg_id, riparian_veg_id, @lkp_brat_vegetation_cis)'
        self.set_value_map(feature_layer, 'veg_density_id', self.project.project_file, 'lkp_brat_dam_density', 'Vegetation Dam Density', expression=veg_expression, parent_container=veg_container, display_index=2)
        editFormConfig.addTab(veg_container)

        # Combined Evidence Group Box
        comb_container = QgsAttributeEditorContainer('Combined Evidence CIS', rootContainer)
        self.set_value_map(feature_layer, 'base_streampower_id', self.project.project_file, 'lkp_brat_base_streampower', 'Base Streampower', parent_container=comb_container, display_index=0)
        self.set_value_map(feature_layer, 'high_streampower_id', self.project.project_file, 'lkp_brat_high_streampower', 'High Streampower', parent_container=comb_container, display_index=1)
        self.set_value_map(feature_layer, 'slope_id', self.project.project_file, 'lkp_brat_slope', 'Slope', parent_container=comb_container, display_index=2)
        comb_expression = 'get_comb_dam_density(veg_density_id, base_streampower_id, high_streampower_id, slope_id,  @lkp_brat_combined_cis)'
        self.set_value_map(feature_layer, 'combined_density_id', self.project.project_file, 'lkp_brat_dam_density', 'Combined Dam Density', expression=comb_expression, parent_container=comb_container, display_index=3)
        editFormConfig.addTab(comb_container)

        # Add Help Button to Form
        self.add_help_action(feature_layer, 'brat-cis', rootContainer)

        feature_layer.setEditFormConfig(editFormConfig)

        feature_layer.editingStarted.connect(self.stop_brat_edit)
        feature_layer.editingStopped.connect(self.stop_brat_edit)

    # QgsActions
    def add_buffer_action(self, feature_layer: QgsVectorLayer, parent_container: QgsAttributeEditorContainer):

        action_text = dedent("""
                            from PyQt5 import QtCore
                            from qgis.PyQt.QtGui import QColor

                            buffers = {"Small":15,
                                    "Large":50}
                            buffer_color = {"Small":QColor(237,10,10,255),
                                            "Large":QColor(237,10,10,255)}
                            preview_layers = {}
                            feats = {}

                            canvas = qgis.utils.iface.mapCanvas()
                            brat_layer = QgsProject.instance().mapLayer('[% @layer_id %]')
                            fid = [% $id %]
                            feature = brat_layer.getFeature(fid)
                            tr = QgsCoordinateTransform(brat_layer.sourceCrs(), QgsCoordinateReferenceSystem("ESRI:102008"), QgsProject.instance())
                            base_geom = feature.geometry()
                            base_geom.transform(tr)

                            for buffer, size in buffers.items():
                                for layer in QgsProject.instance().mapLayersByName(f"QRIS BRAT CIS {buffer} Buffer Context"):
                                    QgsProject.instance().removeMapLayer(layer.id())
                                preview_layers[buffer] = QgsVectorLayer('polygon?crs=esri:102008', f"QRIS BRAT CIS {buffer} Buffer Context", 'memory')
                                # preview_layers[buffer].setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setColor(QColor(0,0,0,0))
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeColor(buffer_color[buffer])
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeStyle(QtCore.Qt.DashLine)
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeWidth(0.5)

                                buffer_geom = base_geom.buffer(size, 10, QgsGeometry.CapFlat, QgsGeometry.JoinStyleRound, 0.0)

                                feats[buffer] = QgsFeature()
                                feats[buffer].setGeometry(buffer_geom)
                                preview_layers[buffer].dataProvider().addFeature(feats[buffer])
                                preview_layers[buffer].commitChanges()

                            QgsProject.instance().addMapLayers([layer for layer in preview_layers.values()])
                            tr_extent = QgsCoordinateTransform(QgsCoordinateReferenceSystem("ESRI:102008"),canvas.mapSettings().destinationCrs(), QgsProject.instance())
                            extent_geom = feats['Large'].geometry()
                            extent_geom.transform(tr_extent)
                            canvas.setExtent(extent_geom.boundingBox())
                            canvas.refresh()
                      """).strip("\n")

        action = QgsAction(1, 'Generate Brat CIS Context Buffers', action_text, None, capture=False, shortTitle='Generate Context', actionScopes={'Feature', 'Layer'})
        feature_layer.actions().addAction(action)
        editorAction = QgsAttributeEditorAction(action, parent_container)
        parent_container.addChildElement(editorAction)

    def stop_brat_edit(self):
        buffers = {"Small": 0.0001,
                   "Large": 0.00025}
        for buffer in buffers.keys():
            for layer in QgsProject.instance().mapLayersByName(f"QRIS BRAT CIS {buffer} Buffer Context"):
                QgsProject.instance().removeMapLayer(layer.id())


# QGSfunctions for field expressions
@ qgsfunction(args='auto', group='QRIS', referenced_columns=[])
def get_veg_dam_density(stream_veg, riparian_veg, rules_string, feature, parent):
    rules = json.loads(rules_string)
    for rule in rules:
        if stream_veg == rule[1] and riparian_veg == rule[2]:
            return rule[3]
    return 1


@ qgsfunction(args='auto', group='QRIS', referenced_columns=[])
def get_comb_dam_density(veg_density, base_power, high_power, slope, cis_rules, feature, parent):
    combined_rules = json.loads(cis_rules)
    for rule in combined_rules:
        if veg_density == rule[1] and base_power == rule[2] and high_power == rule[3] and slope == rule[4]:
            return rule[5]
    return 1  # Default output is None if not in rules table
