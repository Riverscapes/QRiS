import os
import json
import sqlite3
from datetime import datetime

from osgeo import ogr

from PyQt5 import QtCore
from qgis.core import Qgis, QgsVectorLayer, QgsMessageLog

from ..model.project import Project
from ..model.raster import Raster
from ..model.profile import Profile
from ..model.pour_point import PourPoint
from ..model.cross_sections import CrossSections
from ..model.sample_frame import SampleFrame
from ..model.scratch_vector import ScratchVector, scratch_gpkg_path
from ..model.event import Event, EVENT_TYPE_LOOKUP
from ..model.event_layer import EventLayer
from ..model.layer import Layer
from ..model.planning_container import PlanningContainer
from ..model.analysis import Analysis
from ..model.attachment import Attachment

def rsxml_import():
    try:
        import rsxml
        QgsMessageLog.logMessage('rsxml imported from system', 'Riverscapes Viewer', Qgis.Info)
    except ImportError:
        QgsMessageLog.logMessage('rsxml not found in system, importing from source', 'Riverscapes Viewer', Qgis.Info)
        rsxml = None
    return rsxml

rsxml = rsxml_import()
from ...__version__ import __version__ as installed_qris_version


ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'

PROJECT_MACHINE_NAME = 'RiverscapesStudio'
DEFAULT_EXPORT_PATH = 'default_export_path'


class RSProject:

    def __init__(self, qris_project: Project):
        
        if not rsxml:
            raise Exception("rsxml module not available, cannot create RSProject")
            return
        
        self.qris_project = qris_project
        self.project_rs_xml_path = os.path.join(os.path.dirname(self.qris_project.project_file), 'project.rs.xml')
        self.warehouse_id = None
        # if the project file already exists, we need to see if it has a warehouse id
        if os.path.exists(self.project_rs_xml_path):

            rs_project_existing = rsxml.project_xml.Project.load_project(self.project_rs_xml_path)
            self.warehouse_id = rs_project_existing.warehouse
        self.out_name = 'qris.gpkg'  # os.path.split(self.qris_project.project_file)[1]
        self.qris_version = ".".join(installed_qris_version.split(".")[:3])

        self.created_on = datetime.now()
        self.project_updated = self.created_on
        if self.qris_project.created_on and isinstance(self.qris_project.created_on, str):
                self.created_on = datetime.strptime(self.qris_project.created_on, "%Y-%m-%d %H:%M:%S")

    def get_project_bounds(self):

        # See if any of the aoi's are specified as bounds in thier metadata
        for aoi in self.qris_project.aois.values():
            if aoi.sample_frame_type != SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                continue
            if aoi.project_bounds:
                # get the bounds from the sample frame features
                db_path = self.qris_project.project_file
                temp_layer = QgsVectorLayer(f'{db_path}|layername=sample_frame_features|subset=sample_frame_id = {aoi.id}', 'temp', 'ogr')
                if temp_layer.isValid() and temp_layer.featureCount() > 0:
                    output_geom = temp_layer.getFeatures().__next__().geometry()
                    extent = output_geom.boundingBox()
                    centroid = output_geom.centroid().asPoint()
                    geojson = output_geom.asJson()
                    geojson_filename = "project_bounds.geojson"
                    geojson_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), geojson_filename).replace("\\", "/"))
                    with open(geojson_path, 'w') as f:
                        f.write(geojson)
                    project_bounds = rsxml.project_xml.ProjectBounds(
                        centroid=rsxml.project_xml.Coords(centroid.x(), centroid.y()),
                        bounding_box=rsxml.project_xml.BoundingBox(
                            minLat=extent.yMinimum(),
                            minLng=extent.xMinimum(),
                            maxLat=extent.yMaximum(),
                            maxLng=extent.xMaximum()),
                        filepath=geojson_filename)
                    return project_bounds
        return None

    def build_project(self):

        metadata_values = [rsxml.project_xml.Meta('QRiS Project Name', self.qris_project.name),
                           rsxml.project_xml.Meta('QRiS Project Description', self.qris_project.description),
                           rsxml.project_xml.Meta('ModelVersion', '1'),
                           rsxml.project_xml.Meta('Project Updated', self.project_updated.strftime("%Y-%m-%dT%H:%M:%S"))
                           ]
        for key, value in self.qris_project.metadata.items():
            # if tags are empty, skip
            if key == "tags":
                continue
            if value == "":
                continue
            if key == "metadata":
                dict_metadata: dict = value
                for k, v in dict_metadata.items():
                    metadata_values.append(rsxml.project_xml.Meta(k, v))
            else:
                metadata_values.append(rsxml.project_xml.Meta(key, value))

        project_bounds = self.get_project_bounds()

        out_project = rsxml.project_xml.Project(name=self.qris_project.name,
                                proj_path=self.project_rs_xml_path,
                                project_type=PROJECT_MACHINE_NAME,
                                meta_data=rsxml.project_xml.MetaData(values=metadata_values),
                                warehouse=self.warehouse_id,
                                description=self.qris_project.description,
                                bounds=project_bounds)
        return out_project

    def build_rasters(self):
        raster_datasets = []
        for raster in self.qris_project.rasters.values():
            # check if raster is surface or context
            if raster.is_context:
                raster_xml_id = f'context_{raster.id}'
            else:
                raster_xml_id = f'surface_{raster.id}'

            raster_datasets.append(
                rsxml.project_xml.Dataset(
                    xml_id=raster_xml_id,
                    name=raster.name,
                    path=raster.path,
                    ds_type='Raster'))
        
        return raster_datasets

    def build_sample_frames(self, sample_frames, sample_frame_type, name):
        
        out_layers = []
        sample_frame: SampleFrame = None
        for sample_frame in sample_frames:
            if not sample_frame.sample_frame_type == sample_frame_type:
                continue

            out_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=sample_frame.view_name,
                                                        name=sample_frame.name,
                                                        ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                        lyr_type=name))
        return out_layers

    def build_profiles(self, profiles):
        out_layers = []
        profile: Profile = None
        for profile in profiles:
            out_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=profile.view_name,
                                                      name=profile.name,
                                                      ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                      lyr_type='profile'))
        return out_layers
    
    def build_cross_sections(self, cross_sections):
        out_layers = []
        cross_section: CrossSections = None
        for cross_section in cross_sections:
            out_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=cross_section.view_name,
                                                      name=cross_section.name,
                                                      ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                      lyr_type='cross_section'))
        return out_layers
    
    def build_pour_points(self):
        out_layers = []
        pour_point: PourPoint = None
        for pour_point in self.qris_project.pour_points.values():
            out_layers.append(rsxml.project_xml.GeopackageLayer(
                lyr_name=pour_point.view_name,
                name=pour_point.name,
                ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                lyr_type='pour_point'))
            out_layers.append(rsxml.project_xml.GeopackageLayer(
                lyr_name=pour_point.catchment.view_name,
                name=pour_point.name,
                ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                lyr_type='catchments'))
        if out_layers:
            # Use the first pour_point for xml_id and name, or set a generic name
            out_gpkg = rsxml.project_xml.Geopackage(
                xml_id=f'pour_points_gpkg',
                name=f'Pour Points',
                path=self.out_name,
                layers=out_layers)
            return out_gpkg
        return None

    def build_context_layers(self):
        # context vectors
        out_gpkg = None
        context_layers = []
        context_vector: ScratchVector = None
        for context_vector in self.qris_project.scratch_vectors.values():
            geom_type: str = None
            with sqlite3.connect(scratch_gpkg_path(self.qris_project.project_file)) as conn:
                curs = conn.cursor()
                curs.execute(f"SELECT geometry_type_name FROM gpkg_geometry_columns WHERE table_name = '{context_vector.fc_name}'")
                geom_type = curs.fetchone()[0]

            context_layers.append(rsxml.project_xml.GeopackageLayer(summary=f'context_{geom_type.lower()}',
                                                        lyr_name=context_vector.fc_name,
                                                        name=context_vector.name,
                                                        ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                        lyr_type='context'))   
        if len(context_layers) > 0:
            out_gpkg = rsxml.project_xml.Geopackage(xml_id=f'context_gpkg',
                                              name=f'Context',
                                              path='context/feature_classes.gpkg',
                                              layers=context_layers)
        return out_gpkg

    def build_events(self, events: dict) -> list:
        all_photo_metadata = {}
        with sqlite3.connect(self.qris_project.project_file) as conn:
            # iterate through dce_points and get metadata for each photo
            curs = conn.cursor()
            curs.execute("SELECT metadata FROM dce_points")
            rows = curs.fetchall()
            for row in rows:
                metadata = json.loads(row[0])
                if 'Photo Path' in metadata:
                    all_photo_metadata[metadata['Photo Path']] = metadata

        # find the Events node in the tree
        event_realizations = []
        event: Event = None
        for event in events:
            if all([layer.feature_count(self.qris_project.project_file) == 0 for layer in event.event_layers]):
                continue
            event_type = EVENT_TYPE_LOOKUP[event.event_type.id]

            # Search for photos for the dce in the photos folder
            photo_datasets = []

            photo_dce_folder = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), f'photos/dce_{str(event.id).zfill(3)}').replace("\\", "/"))
            # list photos in the photos folder
            if os.path.exists(photo_dce_folder):
                for photo in os.listdir(photo_dce_folder):
                    photo_metadata = all_photo_metadata[photo]
                    photo_id = os.path.splitext(photo)[0]
                    # get the lat long of the photo
                    photo_meta = rsxml.project_xml.MetaData(values=[rsxml.project_xml.Meta('lat', photo_metadata['latitude']),
                                                    rsxml.project_xml.Meta('long', photo_metadata['longitude']),
                                                    rsxml.project_xml.Meta('timestamp', photo_metadata['timestamp'])
                                                    ])

                    photo_datasets.append(rsxml.project_xml.Dataset(xml_id=photo_id,
                                                    name=photo,
                                                    path=f'photos/dce_{str(event.id).zfill(3)}/{photo}',
                                                    meta_data=photo_meta,
                                                    ds_type='Image'))

            meta = rsxml.project_xml.MetaData(values=[rsxml.project_xml.Meta(event_type, "")])
            # prepare the datasets
            geopackage_layers = []
            layer: EventLayer = None
            for layer in event.event_layers:
                if layer.feature_count(self.qris_project.project_file) == 0:
                    continue
                fc_name = Layer.DCE_LAYER_NAMES.get(layer.layer.geom_type, None)
                if fc_name is None:
                    continue

                gp_lyr = rsxml.project_xml.GeopackageLayer(lyr_name=layer.view_name,
                                                name=layer.name,
                                                ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                lyr_type=layer.layer.layer_id)
                geopackage_layers.append(gp_lyr)

            events_gpkg = rsxml.project_xml.Geopackage(xml_id=f'dce_{event.id}_gpkg',
                                            name=f'{event.name}',
                                            path=self.out_name,
                                            layers=geopackage_layers)


            event_creation = event.get_created_on(self.qris_project.project_file)
            if isinstance(event_creation, str):
                try:
                    event_creation = datetime.strptime(event_creation, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    event_creation = datetime.now()  # fallback if format is wrong

            realization = rsxml.project_xml.Realization(
                xml_id=f'realization_qris_{event.id}',
                name=event.name,
                date_created=event_creation,
                product_version=self.qris_version,
                datasets=[events_gpkg] + photo_datasets,
                meta_data=meta
            )

            # add description if it exists
            if event.description:
                realization.description = event.description

            event_realizations.append(realization)
        
        return event_realizations

    def build_planning_containers(self):

        planning_containter_realizations = []
        planning_container: PlanningContainer = None
        for planning_container in self.qris_project.planning_containers.values():
            if len(planning_container.planning_events) == 0:
                continue
            planning_events = [self.qris_project.events[event_id] for event_id in planning_container.planning_events.keys() ]
            event_realizations = self.build_events(planning_events)
            date_created = planning_container.get_created_on(self.qris_project.project_file)
            if isinstance(date_created, str):
                try:
                    date_created = datetime.strptime(date_created, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_created = datetime.now()

            # Build metadata entries for each event in the planning container
            meta_values = []
            for event in planning_events:
                meta_values.append(rsxml.project_xml.Meta(
                    f'Planning Event {event.id}',
                    f'Name: {event.name}, Type: {EVENT_TYPE_LOOKUP[event.event_type.id]}'
                ))

            meta_data = rsxml.project_xml.MetaData(values=meta_values)

            planning_container_realization = rsxml.project_xml.Realization(
                xml_id=f'planning_container_{planning_container.id}',
                name=planning_container.name,
                date_created=date_created,
                product_version=self.qris_version,
                datasets=[],
                meta_data=meta_data
            )

            planning_containter_realizations.append(planning_container_realization)

        return planning_containter_realizations


    def build_analyses(self):

        analysis_realizations = []
        analysis: Analysis = None
        for analysis in self.qris_project.analyses.values():
            geopackage_layers = []
            gp_lyr = rsxml.project_xml.GeopackageLayer(lyr_name=analysis.view_name,
                                            name=analysis.name,
                                            ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                            lyr_type='analysis')
            geopackage_layers.append(gp_lyr)
            analysis_gpkg = rsxml.project_xml.Geopackage(xml_id=f'{analysis.id}_gpkg',
                                                name=f'{analysis.name}',
                                                path=self.out_name,
                                                layers=geopackage_layers)
            date_created = analysis.get_created_on(self.qris_project.project_file)
            if isinstance(date_created, str):
                try:
                    date_created = datetime.strptime(date_created, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_created = datetime.now()

            realization = rsxml.project_xml.Realization(
                xml_id=f'analysis_{analysis.id}',
                name=analysis.name,
                date_created=date_created,
                product_version=self.qris_version,
                datasets=[analysis_gpkg]
            )
            analysis_realizations.append(realization)

        return analysis_realizations

    def build_attachments(self):
        # Attachments
        attachments = []
        meta_values = []
        attachment: Attachment = None
        for attachment in self.qris_project.attachments.values():
            if attachment.attachment_type == Attachment.TYPE_FILE:
                attachments.append(rsxml.project_xml.Dataset(
                    xml_id=f'attachment_{attachment.id}',
                    name=attachment.name,
                    path=f'attachments/{attachment.path}',
                    ds_type='File'))
            elif attachment.attachment_type == Attachment.TYPE_WEB_LINK:
                # Create a metadata entry for web link
                meta_values.append(rsxml.project_xml.Meta(
                    f'Web Link {attachment.id}',
                    f'Name: {attachment.name}, URL: {attachment.path}'
                ))

        meta_data = rsxml.project_xml.MetaData(values=meta_values) if meta_values else None

        attachments_realization = rsxml.project_xml.Realization(
            xml_id='attachments',
            name='Attachments',
            date_created=self.created_on,
            product_version=self.qris_version,
            datasets=attachments,
            meta_data=meta_data
        )

        return attachments_realization

    def write(self):

        if not rsxml:
            return
        self.rs_project = self.build_project()
        
        raster_datasets = self.build_rasters()
        
        input_layers = []
        input_layers.extend(self.build_sample_frames(self.qris_project.valley_bottoms.values(), SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE, 'valley_bottom'))
        input_layers.extend(self.build_sample_frames(self.qris_project.aois.values(), SampleFrame.AOI_SAMPLE_FRAME_TYPE, 'aoi'))
        input_layers.extend(self.build_sample_frames(self.qris_project.sample_frames.values(), SampleFrame.SAMPLE_FRAME_TYPE, 'sample_frame'))
        input_layers.extend(self.build_profiles(self.qris_project.profiles.values()))
        input_layers.extend(self.build_cross_sections(self.qris_project.cross_sections.values()))

        inputs_gpkg = rsxml.project_xml.Geopackage(xml_id=f'inputs_gpkg',
                                       name=f'Inputs',
                                       path=self.out_name,
                                       layers=input_layers)
        
        pour_point_gpkg = self.build_pour_points()
        context_gpkg = self.build_context_layers()
        
        out_gpkgs = [gpkg for gpkg in [inputs_gpkg, pour_point_gpkg, context_gpkg] if gpkg is not None]


        self.rs_project.realizations.append(rsxml.project_xml.Realization(
            xml_id=f'inputs',
            name='Inputs',
            date_created=self.created_on,
            product_version=self.qris_version,
            datasets=raster_datasets + out_gpkgs))


        events_realizations = self.build_events(self.qris_project.events.values())
        planning_container_realizations = self.build_planning_containers()
        analyses_realizations = self.build_analyses()
        attachments_realizations = self.build_attachments()

        self.rs_project.realizations.extend(events_realizations)
        self.rs_project.realizations.extend(planning_container_realizations)
        self.rs_project.realizations.extend(analyses_realizations)
        self.rs_project.realizations.append(attachments_realizations)

        self.rs_project.write()