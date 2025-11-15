import os
import json
import shutil
import sqlite3
import re

from osgeo import ogr

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import QSettings

from ..model.event import Event
from ..model.planning_container import PlanningContainer
from ..model.analysis import Analysis
from ..model.profile import Profile
from ..model.pour_point import PourPoint
from ..model.cross_sections import CrossSections
from ..model.project import Project as QRiSProject
from ..model.raster import Raster
from ..model.scratch_vector import ScratchVector, scratch_gpkg_path
from ..model.stream_gage import StreamGage
from ..model.sample_frame import SampleFrame
from ..model.attachment import Attachment, attachments_path, parse_posix_path

from .utilities import add_standard_form_buttons, message_box

# Puting these here for now to avoid circular imports - source: qris_toolbar.py
ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'

PROJECT_MACHINE_NAME = 'RiverscapesStudio'
DEFAULT_EXPORT_PATH = 'default_export_path'


class FrmExportProject(QtWidgets.QDialog):

    def __init__(self, parent, project: QRiSProject, outpath: str = None):
        super().__init__(parent)

        self.qris_project = project

        # Layer Model
        self.export_layers_model = QtGui.QStandardItemModel()
        self.export_layers_model.itemChanged.connect(self.handle_item_changed)

        self.setWindowTitle("Export QRiS to Riverscapes Studio Project")
        self.setupUi()

        if outpath is not None:
            self.base_folder = outpath
        else:
            settings = QSettings(ORGANIZATION, APPNAME)
            self.base_folder = settings.value(DEFAULT_EXPORT_PATH, '').replace("/", "\\")
        if self.base_folder == "":
            # use the parent of the project folder
            self.base_folder = os.path.dirname(os.path.dirname(self.qris_project.project_file))
        self.set_output_path()

        # Inputs
        inputs_node = QtGui.QStandardItem("Inputs")
        inputs_node.setCheckable(True)
        inputs_node.setCheckState(QtCore.Qt.PartiallyChecked)

        # Riverscapes Node
        riverscapes_node = QtGui.QStandardItem("Riverscapes")
        riverscapes_node.setCheckable(True)
        riverscapes_node.setCheckState(QtCore.Qt.Checked)
        for valley_bottom in self.qris_project.valley_bottoms.values():
            add_to_node(riverscapes_node, valley_bottom, valley_bottom.name)
        inputs_node.appendRow(riverscapes_node)

        # AOIs
        aois_node = QtGui.QStandardItem("AOIs")
        aois_node.setCheckable(True)
        aois_node.setCheckState(QtCore.Qt.Checked)
        for aoi in self.qris_project.aois.values():
            add_to_node(aois_node, aoi, aoi.name)
        inputs_node.appendRow(aois_node)

        # Sample Frames
        sample_frames_node = QtGui.QStandardItem("Sample Frames")
        sample_frames_node.setCheckable(True)
        sample_frames_node.setCheckState(QtCore.Qt.Checked)
        for sample_frame in self.qris_project.sample_frames.values():
            add_to_node(sample_frames_node, sample_frame, sample_frame.name)
        inputs_node.appendRow(sample_frames_node)

        # Profiles
        profiles_node = QtGui.QStandardItem("Profiles")
        profiles_node.setCheckable(True)
        profiles_node.setCheckState(QtCore.Qt.Checked)
        for profile in self.qris_project.profiles.values():
            add_to_node(profiles_node, profile, profile.name)
        inputs_node.appendRow(profiles_node)

        # Cross Sections
        xsections_node = QtGui.QStandardItem("Cross Sections")
        xsections_node.setCheckable(True)
        xsections_node.setCheckState(QtCore.Qt.Checked)
        for xsection in self.qris_project.cross_sections.values():
            add_to_node(xsections_node, xsection, xsection.name)
        inputs_node.appendRow(xsections_node)

        # Surfaces
        surfaces_node = QtGui.QStandardItem("Surfaces")
        surfaces_node.setCheckable(True)
        for surface in self.qris_project.rasters.values():
            if surface.is_context:
                continue
            add_to_node(surfaces_node, surface, surface.name, checked=False)
        inputs_node.appendRow(surfaces_node)
        self.export_layers_model.appendRow(inputs_node)

        # Context
        context_node = QtGui.QStandardItem("Context")
        context_node.setCheckable(True)
        context_node.setCheckState(QtCore.Qt.Checked)

        # Pour Points
        pour_points_node = QtGui.QStandardItem("Watershed Catchments")
        pour_points_node.setCheckable(True)
        pour_points_node.setCheckState(QtCore.Qt.Checked)
        for pour_point in self.qris_project.pour_points.values():
            add_to_node(pour_points_node, pour_point, pour_point.name)
        context_node.appendRow(pour_points_node)

        for context_vector in self.qris_project.scratch_vectors.values():
            add_to_node(context_node, context_vector, context_vector.name)
        for context in self.qris_project.rasters.values():
            if not context.is_context:
                continue
            add_to_node(context_node, context, context.name)
        inputs_node.appendRow(context_node)

        # DCE and Designs
        events_node = QtGui.QStandardItem("Data Capture Events")
        events_node.setCheckable(True)
        events_node.setCheckState(QtCore.Qt.Checked)
        for event in self.qris_project.events.values():
            add_to_node(events_node, event, event.name)
        self.export_layers_model.appendRow(events_node)

        planning_containers_node = QtGui.QStandardItem("Planning Containers")
        planning_containers_node.setCheckable(True)
        planning_containers_node.setCheckState(QtCore.Qt.Checked)
        for pc in self.qris_project.planning_containers.values():
            add_to_node(planning_containers_node, pc, pc.name)
        self.export_layers_model.appendRow(planning_containers_node)

        # Analysis
        analyses_node = QtGui.QStandardItem("Analyses")
        analyses_node.setCheckable(True)
        analyses_node.setCheckState(QtCore.Qt.Checked)
        for analysis in self.qris_project.analyses.values():
            add_to_node(analyses_node, analysis, analysis.name)
        self.export_layers_model.appendRow(analyses_node)

        # Attachments Node
        attachments_node = QtGui.QStandardItem("Attachments")
        attachments_node.setCheckable(True)
        attachments_node.setCheckState(QtCore.Qt.Checked)

        for attachment in self.qris_project.attachments.values():
            label = f"{attachment.name} ({'File' if attachment.attachment_type == Attachment.TYPE_FILE else 'Web Link'})"
            add_to_node(attachments_node, attachment, label)

        self.export_layers_model.appendRow(attachments_node)

        # Layer Tree
        self.export_tree.setModel(self.export_layers_model)
        self.export_tree.setUniformRowHeights(True)
        self.export_tree.setAnimated(True)
        self.export_tree.setIndentation(20)
        self.export_tree.setSortingEnabled(False)
        self.export_tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.export_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.export_tree.expandAll()

    def handle_item_changed(self, item: QtGui.QStandardItem):
        if item.hasChildren():
            self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
            self.update_child_check_state(item)
            self.export_layers_model.itemChanged.connect(self.handle_item_changed)
        self.update_check_state(item.parent())

    def update_child_check_state(self, item: QtGui.QStandardItem):
        for i in range(item.rowCount()):
            child = item.child(i)
            if child is not None:
                child.setCheckState(item.checkState())
                if child.hasChildren():
                    self.update_child_check_state(child)

    def update_check_state(self, item: QtGui.QStandardItem):
        if item is not None and item.hasChildren():
            check_states = [item.child(i).checkState() for i in range(item.rowCount())]
            if all(state == QtCore.Qt.Checked for state in check_states):
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.Checked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            elif all(state == QtCore.Qt.Unchecked for state in check_states):
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            else:
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.PartiallyChecked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            self.update_check_state(item.parent())

    def set_output_path(self):

        if self.base_folder == "":
            return

        name = ""

        if self.chk_qris_export_folder.isChecked():
            name = re.sub(r'[ .,:/\\?!\'"<>\|\*\(\)\[\]\{\}]', '_', self.txt_rs_name.text())

        outpath = os.path.join(self.base_folder, name)
        
        if self.chk_qris_export_folder.isChecked():
            if os.path.exists(outpath):
                outpath = outpath + "_export"
        # Fix the path separators for Windows
        outpath = outpath.replace("/", "\\")
        self.txt_outpath.setText(outpath)

    def accept(self) -> None:
        if not self.validate_tree():
            return
        # use only the first three components of the version

        if self.txt_rs_name.text() == "":
            message_box("Project Name", "Please enter a name for the Riverscapes project.")
            return

        if self.txt_outpath.text() == "":
            message_box("Output Path", "Please select an output path for the Riverscapes project.")
            return

        outpath = self.txt_outpath.text()
        if not os.path.isdir(os.path.dirname(outpath)):
            message_box("Invalid Output Path", "The output path is invalid. Please select a valid output path.")
            return

        # check if output directory is empty. If so, prompt user to overwrite or cancel
        if os.path.exists(self.txt_outpath.text()):
            if len(os.listdir(self.txt_outpath.text())) > 0:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("The selected output folder is not empty. Do you want to overwrite it?")
                msg.setWindowTitle("Overwrite Output Folder?")
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
                msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
                ret = msg.exec_()
                if ret == QtWidgets.QMessageBox.Cancel:
                    return

        # create a new project folder if it doesn't exist
        if not os.path.exists(self.txt_outpath.text()):
            os.makedirs(self.txt_outpath.text())

        # copy the geopackage layers to the new project folder
        out_name = 'qris.gpkg'  # os.path.split(self.qris_project.project_file)[1]
        out_geopackage = os.path.abspath(os.path.join(self.txt_outpath.text(), out_name).replace("\\", "/"))

        shutil.copy(self.qris_project.project_file, out_geopackage)

        date_created = QtCore.QDateTime.currentDateTime()

        keep_layers: dict = {}  # {layer_name: {id_field: id_field_name, id_values: [id_values]}}

        # Inputs
        inputs_node = self.export_layers_model.findItems("Inputs")[0]

        # Surface Rasters
        raster_node = self.find_child_node(inputs_node, "Surfaces")
        if raster_node:
            for i in range(raster_node.rowCount()):
                raster_item = raster_node.child(i)
                if raster_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                raster: Raster = raster_item.data(QtCore.Qt.UserRole)

                if 'rasters' not in keep_layers:
                    keep_layers['rasters'] = {'id_field': 'id', 'id_values': []}
                keep_layers['rasters']['id_values'].append(str(raster.id))

                src_raster_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), raster.path).replace("\\", "/"))
                out_raster_path = os.path.abspath(os.path.join(self.txt_outpath.text(), raster.path).replace("\\", "/"))
                if not os.path.exists(os.path.dirname(out_raster_path)):
                    os.makedirs(os.path.dirname(out_raster_path))
                shutil.copy(src_raster_path, out_raster_path)

        # Valley Bottoms
        valley_bottom_node = self.find_child_node(inputs_node, "Riverscapes")
        if valley_bottom_node:
            for i in range(valley_bottom_node.rowCount()):
                valley_bottom_item = valley_bottom_node.child(i)
                if valley_bottom_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                valley_bottom: SampleFrame = valley_bottom_item.data(QtCore.Qt.UserRole)
                if not valley_bottom.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                    continue

                if 'sample_frame_features' not in keep_layers:
                    keep_layers['sample_frame_features'] = {'id_field': 'sample_frame_id', 'id_values': []}
                keep_layers['sample_frame_features']['id_values'].append(str(valley_bottom.id))
                if 'sample_frames' not in keep_layers:
                    keep_layers['sample_frames'] = {'id_field': 'id', 'id_values': []}
                keep_layers['sample_frames']['id_values'].append(str(valley_bottom.id))

        # AOIs
        aoi_node = self.find_child_node(inputs_node, "AOIs")
        if aoi_node:
            for i in range(aoi_node.rowCount()):
                aoi_item = aoi_node.child(i)
                if aoi_item.checkState() == QtCore.Qt.Unchecked:
                    continue

                aoi: SampleFrame = aoi_item.data(QtCore.Qt.UserRole)
                if not aoi.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                    continue

                if 'sample_frame_features' not in keep_layers:
                    keep_layers['sample_frame_features'] = {'id_field': 'sample_frame_id', 'id_values': []}
                keep_layers['sample_frame_features']['id_values'].append(str(aoi.id))
                if 'sample_frames' not in keep_layers:
                    keep_layers['sample_frames'] = {'id_field': 'id', 'id_values': []}
                keep_layers['sample_frames']['id_values'].append(str(aoi.id))

        # Sample Frames
        sample_frame_node = self.find_child_node(inputs_node, "Sample Frames")
        if sample_frame_node:
            for i in range(sample_frame_node.rowCount()):
                sample_frame_item = sample_frame_node.child(i)
                if sample_frame_item.checkState() == QtCore.Qt.Unchecked:
                    continue

                sample_frame: SampleFrame = sample_frame_item.data(QtCore.Qt.UserRole)

                if 'sample_frame_features' not in keep_layers:
                    keep_layers['sample_frame_features'] = {'id_field': 'sample_frame_id', 'id_values': []}
                keep_layers['sample_frame_features']['id_values'].append(str(sample_frame.id))
                if 'sample_frames' not in keep_layers:
                    keep_layers['sample_frames'] = {'id_field': 'id', 'id_values': []}
                keep_layers['sample_frames']['id_values'].append(str(sample_frame.id))

        # Profiles
        profile_node = self.find_child_node(inputs_node, "Profiles")
        if profile_node:
            for i in range(profile_node.rowCount()):
                profile_item = profile_node.child(i)
                if profile_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                profile: Profile = profile_item.data(QtCore.Qt.UserRole)
                profile_fc = 'profile_centerlines' if profile.profile_type_id == 2 else 'profile_features'

                if profile_fc not in keep_layers:
                    keep_layers[profile_fc] = {'id_field': 'profile_id', 'id_values': []}
                keep_layers[profile_fc]['id_values'].append(str(profile.id))
                if 'profiles' not in keep_layers:
                    keep_layers['profiles'] = {'id_field': 'id', 'id_values': []}
                keep_layers['profiles']['id_values'].append(str(profile.id))

        # Cross Sections
        xsection_node = self.find_child_node(inputs_node, "Cross Sections")
        if xsection_node:
            for i in range(xsection_node.rowCount()):
                xsection_item = xsection_node.child(i)
                if xsection_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                xsection: CrossSections = xsection_item.data(QtCore.Qt.UserRole)

                if 'cross_section_features' not in keep_layers:
                    keep_layers['cross_section_features'] = {'id_field': 'cross_section_id', 'id_values': []}
                keep_layers['cross_section_features']['id_values'].append(str(xsection.id))
                if 'cross_sections' not in keep_layers:
                    keep_layers['cross_sections'] = {'id_field': 'id', 'id_values': []}
                keep_layers['cross_sections']['id_values'].append(str(xsection.id))

        context_node = self.find_child_node(inputs_node, "Context")

        # need to prepare the Watershed catchments (pour points)
        pour_point_gpkgs = []
        pour_point_node = self.find_child_node(context_node, "Watershed Catchments")
        if pour_point_node:
            for i in range(pour_point_node.rowCount()):
                pour_point_item = pour_point_node.child(i)
                if pour_point_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                pour_point: PourPoint = pour_point_item.data(QtCore.Qt.UserRole)

                if 'pour_points' not in keep_layers:
                    keep_layers['pour_points'] = {'id_field': 'fid', 'id_values': []}
                keep_layers['pour_points']['id_values'].append(str(pour_point.id))

                if 'catchments' not in keep_layers:
                    keep_layers['catchments'] = {'id_field': 'pour_point_id', 'id_values': []}
                keep_layers['catchments']['id_values'].append(str(pour_point.id))

        # context vectors
        keep_context_layers = []
        for i in range(context_node.rowCount()):
            context_item = context_node.child(i)
            # Skip if this is the Watershed Catchments
            if context_item.text() == "Watershed Catchments":
                continue
            if context_item.checkState() == QtCore.Qt.Unchecked:
                continue
            context = context_item.data(QtCore.Qt.UserRole)
            if isinstance(context, Raster):
                raster: Raster = context_item.data(QtCore.Qt.UserRole)

                if 'rasters' not in keep_layers:
                    keep_layers['rasters'] = {'id_field': 'id', 'id_values': []}
                keep_layers['rasters']['id_values'].append(str(raster.id))

                raster_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), raster.path).replace("\\", "/"))
                out_raster_path = os.path.abspath(os.path.join(self.txt_outpath.text(), raster.path).replace("\\", "/"))
                if not os.path.exists(os.path.dirname(out_raster_path)):
                    os.makedirs(os.path.dirname(out_raster_path))
                shutil.copy(raster_path, out_raster_path)
            else:
                context_vector: ScratchVector = context_item.data(QtCore.Qt.UserRole)
                # get the geom type for the feature class
                geom_type: str = None
                with sqlite3.connect(scratch_gpkg_path(self.qris_project.project_file)) as conn:
                    curs = conn.cursor()
                    curs.execute(f"SELECT geometry_type_name FROM gpkg_geometry_columns WHERE table_name = '{context_vector.fc_name}'")
                    geom_type = curs.fetchone()[0]
                keep_context_layers.append(context_vector.fc_name)

                if 'scratch_vectors' not in keep_layers:
                    keep_layers['scratch_vectors'] = {'id_field': 'id', 'id_values': []}
                keep_layers['scratch_vectors']['id_values'].append(str(context_vector.id))

        # out_gpkgs = [inputs_gpkg]
        if len(keep_context_layers) > 0:
            # create the context geopackage and copy the layers
            context_gpkg = os.path.abspath(os.path.join(self.txt_outpath.text(), "context", "feature_classes.gpkg").replace("\\", "/"))
            if not os.path.exists(os.path.dirname(context_gpkg)):
                os.makedirs(os.path.dirname(context_gpkg))
            src_ds = ogr.Open(scratch_gpkg_path(self.qris_project.project_file), 0)

            # create a new GeoPackage
            dst_ds = ogr.GetDriverByName('GPKG').CreateDataSource(context_gpkg)

            # iterate over the layers in the source GeoPackage
            for i in range(src_ds.GetLayerCount()):
                src_layer = src_ds.GetLayerByIndex(i)
                # check if the layer is in the context_layers list
                if src_layer.GetName() not in keep_context_layers:
                    continue
                # create the layer in the destination GeoPackage
                dst_layer = dst_ds.CreateLayer(src_layer.GetName(), geom_type=src_layer.GetGeomType(), srs=src_layer.GetSpatialRef())
                # copy the fields
                for j in range(src_layer.GetLayerDefn().GetFieldCount()):
                    src_field = src_layer.GetLayerDefn().GetFieldDefn(j)
                    dst_layer.CreateField(src_field)
                # copy the features
                for src_feature in src_layer:
                    dst_feature = ogr.Feature(dst_layer.GetLayerDefn())
                    dst_feature.SetGeometry(src_feature.GetGeometryRef().Clone())
                    for j in range(src_layer.GetLayerDefn().GetFieldCount()):
                        dst_feature.SetField(j, src_feature.GetField(j))
                    dst_layer.CreateFeature(dst_feature)
                    dst_feature = None

            # close the GeoPackages
            src_ds = None
            dst_ds = None

        all_photo_metadata = {}
        with sqlite3.connect(out_geopackage) as conn:
            # iterate through dce_points and get metadata for each photo
            curs = conn.cursor()
            curs.execute("SELECT metadata FROM dce_points")
            rows = curs.fetchall()
            for row in rows:
                metadata = json.loads(row[0])
                if 'Photo Path' in metadata:
                    all_photo_metadata[metadata['Photo Path']] = metadata

        # find the Events node in the tree
        events_nodes = self.export_layers_model.findItems("Data Capture Events")
        if events_nodes:
            events_node = events_nodes[0]
            for i in range(events_node.rowCount()):
                event_item = events_node.child(i)
                if event_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                event: Event = event_item.data(QtCore.Qt.UserRole)
                # if all([layer.feature_count(self.qris_project.project_file) == 0 for layer in event.event_layers]):
                #     continue


                if 'events' not in keep_layers:
                    keep_layers['events'] = {'id_field': 'id', 'id_values': []}
                keep_layers['events']['id_values'].append(str(event.id))
                if 'event_layers' not in keep_layers:
                    keep_layers['event_layers'] = {'id_field': 'event_id', 'id_values': []}
                keep_layers['event_layers']['id_values'].append(str(event.id))
                if 'event_rasters' not in keep_layers:
                    keep_layers['event_rasters'] = {'id_field': 'event_id', 'id_values': []}
                keep_layers['event_rasters']['id_values'].append(str(event.id))

                # Search for photos for the dce in the photos folder
                source_photos_dir = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
                photo_dce_folder = os.path.abspath(os.path.join(self.txt_outpath.text(), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
                if os.path.exists(source_photos_dir):
                    shutil.copytree(source_photos_dir, photo_dce_folder)

                # prepare the datasets
                for layer in event.event_layers:
                    if self.chk_exclude_empty_layers.isChecked() and layer.feature_count(self.qris_project.project_file) == 0:
                        continue
                    geom_type = layer.layer.geom_type
                    if geom_type == "Point":
                        fc_name = 'dce_points'
                    elif geom_type == "Linestring":
                        fc_name = 'dce_lines'
                    elif geom_type == "Polygon":
                        fc_name = 'dce_polygons'
                    else:
                        continue

                    if fc_name not in keep_layers:
                        keep_layers[fc_name] = {'id_field': 'event_layer_id', 'id_values': []}
                    keep_layers[fc_name]['id_values'].append(str(layer.layer.id))

        # add planning containers
        planning_containers_nodes = self.export_layers_model.findItems("Planning Containers")
        if planning_containers_nodes:
            planning_container_node = planning_containers_nodes[0]
            for i in range(planning_container_node.rowCount()):
                planning_container_item = planning_container_node.child(i)
                if planning_container_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                planning_container: PlanningContainer = planning_container_item.data(QtCore.Qt.UserRole)
                if len(planning_container.planning_events) == 0:
                    continue
                if 'planning_containers' not in keep_layers:
                    keep_layers['planning_containers'] = {'id_field': 'id', 'id_values': []}
                keep_layers['planning_containers']['id_values'].append(str(planning_container.id))

        # add analyses
        analysis_nodes = self.export_layers_model.findItems("Analyses")
        if analysis_nodes:
            analysis_node = analysis_nodes[0]
            for i in range(analysis_node.rowCount()):
                analysis_item = analysis_node.child(i)
                if analysis_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                analysis: Analysis = analysis_item.data(QtCore.Qt.UserRole)

                # analysis: Analysis = analysis
                sample_frame: SampleFrame = analysis.sample_frame

                # flatten the table of analysis metrics
                analysis_metrics = []
                for metric_id, metric in analysis.analysis_metrics.items():
                    analysis_metrics.append([metric_id, metric.level_id])

                if 'analyses' not in keep_layers:
                    keep_layers['analyses'] = {'id_field': 'id', 'id_values': []}
                keep_layers['analyses']['id_values'].append(str(analysis.id))
                if 'analysis_metrics' not in keep_layers:
                    keep_layers['analysis_metrics'] = {'id_field': 'analysis_id', 'id_values': []}
                keep_layers['analysis_metrics']['id_values'].append(str(analysis.id))

        # Attachments
        attachments_nodes = self.export_layers_model.findItems("Attachments")
        if attachments_nodes:
            attachments_node = attachments_nodes[0]
            for i in range(attachments_node.rowCount()):
                child = attachments_node.child(i)
                if child.checkState() == QtCore.Qt.Unchecked:
                    continue
                attachment: Attachment = child.data(QtCore.Qt.UserRole)
                # Process the attachment (e.g., copy files, collect web links)
                if attachment.attachment_type == Attachment.TYPE_FILE:
                    dest_attachments_folder = os.path.abspath(os.path.join(self.txt_outpath.text(), "attachments").replace("\\", "/"))
                    if not os.path.exists(dest_attachments_folder):
                        os.makedirs(dest_attachments_folder)
                    src_path = attachment.project_path(self.qris_project.project_file)
                    dst_path = attachment.project_path(dest_attachments_folder)
                    if os.path.exists(src_path):
                        shutil.copy(src_path, dst_path)

                # elif attachment.attachment_type == Attachment.TYPE_WEB_LINK:
                #     pass
                
                if 'attachments' not in keep_layers:
                    keep_layers['attachments'] = {'id_field': 'attachment_id', 'id_values': []}
                keep_layers['attachments']['id_values'].append(str(attachment.id))

        # open the geopackage using ogr
        ds_gpkg: ogr.DataSource = ogr.Open(out_geopackage, 1)
        for layer in ['analyses', 'catchments', 'cross_sections', 'cross_section_features', 'dce_lines', 'dce_points', 'dce_polygons', 'events', 'event_layers', 'pour_points', 'profile_centerlines', 'profile_features', 'profiles', 'rasters', 'scratch_vectors', 'sample_frame_features', 'sample_frames', 'attachments', 'planning_containers']:
            # get the layer
            lyr: ogr.Layer = ds_gpkg.GetLayerByName(layer)
            # remove all features that are not in the keep list
            if layer in keep_layers:
                keep_layer = keep_layers[layer]
                lyr.SetAttributeFilter(f"{keep_layer['id_field']} NOT IN ({', '.join(keep_layer['id_values'])})")
            if lyr.GetFeatureCount() != 0:
                for feat in lyr:
                    lyr.DeleteFeature(feat.GetFID())
            lyr.SetAttributeFilter(None)
            lyr = None
        ds_gpkg = None

        # use sqlite3 to vacuum the geopackage
        with sqlite3.connect(out_geopackage) as conn:

            # Delete orphaned records
            curs = conn.cursor()
            curs.execute("DELETE FROM event_rasters WHERE event_id NOT IN (SELECT id FROM events)")
            curs.execute("DELETE FROM planning_container_events WHERE planning_container_id NOT IN (SELECT id FROM planning_containers)")
            curs.execute("DELETE FROM metric_values WHERE analysis_id NOT IN (SELECT id FROM analyses)")
            curs.execute("DELETE FROM analysis_metrics WHERE analysis_id NOT IN (SELECT id FROM analyses)")
            conn.commit()  # Commit the transaction before executing VACUUM

            # Write project name and description
            project_name = self.txt_rs_name.text()
            project_description = self.txt_description.toPlainText()
            conn.execute("UPDATE projects SET name = ?, description = ? WHERE id = 1", (project_name, project_description))
            conn.commit()
            conn.execute("VACUUM")

        return super().accept()

    def find_child_node(self, node: QtWidgets.QTreeWidgetItem, tag: str):

        for i in range(node.rowCount()):
            child = node.child(i)
            if child.text() == tag:
                return child
        return None

    def browse_path(self):

        if self.txt_outpath.text() is not None and self.txt_outpath.text() != "":
            basepath = self.txt_outpath.text()
        else:
            basepath = os.path.dirname(self.qris_project.project_file)
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', basepath, QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            # check if a project.rs.xml file already exists in the selected folder
            if os.path.exists(path):
                if os.path.exists(os.path.join(path, "project.rs.xml")):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Warning)
                    msg.setText("A Riverscapes project file already exists in the selected folder. Do you want to overwrite it?")
                    msg.setWindowTitle("Overwrite Project File?")
                    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
                    msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                    msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
                    ret = msg.exec_()
                    if ret == QtWidgets.QMessageBox.Cancel:
                        return
        self.base_folder = path.replace("/", "\\")
        self.set_output_path()

    def set_checkbox_state(self, state: bool):

        for i in range(self.export_layers_model.rowCount()):
            item = self.export_layers_model.item(i)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    # def browse_existing(self):

    #     path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Existing Project', '', 'Riverscapes Project (*.rs.xml)')[0]
    #     if path:
    #         self.txt_existing_path.setText(path)

    # def change_new_or_existing(self):

    #     if self.rdo_new.isChecked():
    #         self.txt_existing_path.setEnabled(False)
    #         self.btn_existing.setEnabled(False)
    #         self.lbl_existing.setEnabled(False)
    #     else:
    #         self.txt_existing_path.setEnabled(True)
    #         self.btn_existing.setEnabled(True)
    #         self.lbl_existing.setEnabled(True)

    def get_checked_items(self, name: str):
        nodes = self.export_layers_model.findItems(name)
        if nodes:
            node = nodes[0]
            for i in range(node.rowCount()):
                item = node.child(i)
                if item.checkState() == QtCore.Qt.Checked:
                    yield item.data(QtCore.Qt.UserRole)

    def validate_tree(self) -> bool:
        
        event_ids = {event.id for event in self.get_checked_items("Data Capture Events")}
        planning_container: PlanningContainer
        for planning_container in self.get_checked_items("Planning Containers"):
            all_checked = all(dce_id in event_ids for dce_id in planning_container.planning_events.keys())
            if not all_checked:
                # item.setCheckState(QtCore.Qt.Unchecked)
                message_box("Export Validation",
                    f"All Data Capture Events associated with '{planning_container.name}' must be selected for export before the Planning Container can be checked.")
                return False
        
        return True
    

    def setupUi(self):

        self.setMinimumSize(500, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        # add grid layout
        self.grid = QtWidgets.QGridLayout()

        # add label and txt box for project name
        self.lbl_project = QtWidgets.QLabel("Riverscapes Project Name")
        self.lbl_project.setToolTip("Enter the name of the Riverscapes project")
        self.grid.addWidget(self.lbl_project, 0, 0, 1, 1)

        self.txt_rs_name = QtWidgets.QLineEdit()
        self.txt_rs_name.setReadOnly(False)
        self.txt_rs_name.setText(self.qris_project.name)
        self.txt_rs_name.textChanged.connect(self.set_output_path)
        self.grid.addWidget(self.txt_rs_name, 0, 1, 1, 1)

        self.chk_qris_export_folder = QtWidgets.QCheckBox("Let QRiS manage the export location")
        self.chk_qris_export_folder.setChecked(True)
        self.chk_qris_export_folder.clicked.connect(self.set_output_path)
        self.grid.addWidget(self.chk_qris_export_folder, 1, 1, 1, 1)

        # add label and horizontal layout with textbox and small button for output path
        self.lbl_output = QtWidgets.QLabel("Output Path")
        self.lbl_output.setToolTip("Select the folder where the Riverscapes project will be saved")
        self.grid.addWidget(self.lbl_output, 2, 0, 1, 1)

        self.horiz_output = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_output, 2, 1, 1, 1)

        self.txt_outpath = QtWidgets.QLineEdit()
        self.txt_outpath.setReadOnly(True)
        self.horiz_output.addWidget(self.txt_outpath)

        self.btn_output = QtWidgets.QPushButton("...")
        self.btn_output.setEnabled(False)
        self.btn_output.setMaximumWidth(30)
        self.btn_output.clicked.connect(self.browse_path)
        self.chk_qris_export_folder.clicked.connect(lambda checked: self.btn_output.setEnabled(not checked))
        self.horiz_output.addWidget(self.btn_output)

        # # Project Bounds
        # self.lbl_project_bounds = QtWidgets.QLabel("Project Bounds")
        # self.lbl_project_bounds.setToolTip("Select the extent of the project. This is used for display purposes on the Riverscapes Data Exchange")
        # self.grid.addWidget(self.lbl_project_bounds, 3, 0, 1, 1, QtCore.Qt.AlignTop)

        # self.vert_project_bounds = QtWidgets.QVBoxLayout()
        # self.grid.addLayout(self.vert_project_bounds, 3, 1, 1, 1)

        # self.horiz_project_bounds_aoi = QtWidgets.QHBoxLayout()
        # self.vert_project_bounds.addLayout(self.horiz_project_bounds_aoi)

        # self.opt_project_bounds_aoi = QtWidgets.QRadioButton("Use AOI or Valley Bottom")
        # self.opt_project_bounds_aoi.setToolTip("Use the extent of a selected AOI or Valley Bottom polygon")
        # self.opt_project_bounds_aoi.setChecked(True)
        # # self.opt_project_bounds_aoi.clicked.connect(self.change_project_bounds)
        # self.horiz_project_bounds_aoi.addWidget(self.opt_project_bounds_aoi)

        # self.cbo_project_bounds_aoi = QtWidgets.QComboBox()
        # self.cbo_project_bounds_aoi.addItem("Select AOI or Valley Bottom")
        # self.cbo_project_bounds_aoi.model().item(0).setEnabled(False)
        # self.horiz_project_bounds_aoi.addWidget(self.cbo_project_bounds_aoi)

        # self.opt_project_bounds_all = QtWidgets.QRadioButton("Use intersection of all QRiS layers")
        # self.opt_project_bounds_all.setToolTip("Use the extent of all QRiS layers in the project")
        # self.opt_project_bounds_all.clicked.connect(self.change_project_bounds)
        # self.vert_project_bounds.addWidget(self.opt_project_bounds_all)

        # New or Existing Project
        # self.lbl_new_or_existing = QtWidgets.QLabel("Export Type")
        # self.lbl_new_or_existing.setToolTip("Select whether to create a new Riverscapes Studio project or update an existing project")
        # self.grid.addWidget(self.lbl_new_or_existing, 4, 0, 1, 1)

        # self.group_new_or_existing = QtWidgets.QButtonGroup(self)

        # self.rdo_new = QtWidgets.QRadioButton("New Riverscapes Studio Project")
        # self.rdo_new.setToolTip("Export as a new Riverscapes Studio project")
        # self.group_new_or_existing.addButton(self.rdo_new)
        # self.rdo_new.setChecked(True)
        # self.rdo_new.clicked.connect(self.change_new_or_existing)
        # self.grid.addWidget(self.rdo_new, 4, 1, 1, 1)

        # self.rdo_existing = QtWidgets.QRadioButton("Update Existing Riverscapes Studio Project")
        # self.rdo_existing.setToolTip("Update a previously uploaded Riverscapes Studio project")
        # self.group_new_or_existing.addButton(self.rdo_existing)
        # self.rdo_existing.clicked.connect(self.change_new_or_existing)
        # self.grid.addWidget(self.rdo_existing, 5, 1, 1, 1)

        # self.horiz_existing = QtWidgets.QHBoxLayout()
        # self.grid.addLayout(self.horiz_existing, 6, 1, 1, 1)

        # self.lbl_existing = QtWidgets.QLabel("Existing Project rs.xml file")
        # self.lbl_existing.setEnabled(False)
        # self.horiz_existing.addWidget(self.lbl_existing)

        # self.txt_existing_path = QtWidgets.QLineEdit()
        # self.txt_existing_path.setReadOnly(True)
        # self.txt_existing_path.setEnabled(False)
        # self.horiz_existing.addWidget(self.txt_existing_path)

        # self.btn_existing = QtWidgets.QPushButton("...")
        # self.btn_existing.setMaximumWidth(30)
        # self.btn_existing.clicked.connect(self.browse_existing)
        # self.btn_existing.setEnabled(False)
        # self.horiz_existing.addWidget(self.btn_existing)

        # add multiline box for description
        self.lbl_description = QtWidgets.QLabel("Description")
        self.grid.addWidget(self.lbl_description, 7, 0, 1, 1, QtCore.Qt.AlignTop)

        self.txt_description = QtWidgets.QTextEdit()
        self.txt_description.setReadOnly(False)
        self.txt_description.setText(self.qris_project.description)
        self.grid.addWidget(self.txt_description, 7, 1, 1, 1)

        # add vertical spacer
        self.vert.addStretch()

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Export Properties')
        self.tabProperties.setLayout(self.grid)

        # Export Tab
        self.vert_export = QtWidgets.QVBoxLayout()
        self.tabExport = QtWidgets.QWidget()
        self.tabExport.setLayout(self.vert_export)
        self.tabs.addTab(self.tabExport, 'Export Layers')

        self.export_tree = QtWidgets.QTreeView()
        self.export_tree.setHeaderHidden(True)
        self.vert_export.addWidget(self.export_tree)

        self.horiz_export = QtWidgets.QHBoxLayout()
        self.vert_export.addLayout(self.horiz_export)

        self.chk_exclude_empty_layers = QtWidgets.QCheckBox("Exclude Empty DCE Layers")
        self.chk_exclude_empty_layers.setChecked(True)
        self.chk_exclude_empty_layers.setToolTip("Check this box to exclude Data Capture Event, Design, AsBuilt and Planning layers that have no features from the export")
        self.horiz_export.addWidget(self.chk_exclude_empty_layers)

        self.horiz_export.addStretch()

        self.btn_select_all = QtWidgets.QPushButton("Select All")
        self.btn_select_all.clicked.connect(lambda: self.set_checkbox_state(True))
        self.horiz_export.addWidget(self.btn_select_all)

        self.btn_select_none = QtWidgets.QPushButton("Select None")
        self.btn_select_none.clicked.connect(lambda: self.set_checkbox_state(False))
        self.horiz_export.addWidget(self.btn_select_none)

        # add standard form buttons
        self.vert.addLayout(add_standard_form_buttons(self, "projects/#export-to-riverscapes-project"))


def add_to_node(node: QtGui.QStandardItem, db_item, label: str, checked: bool=True):
    """
    Adds a new item to the specified node in the tree view.
    """

    item = QtGui.QStandardItem(label)
    item.setCheckable(True)
    item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
    item.setData(db_item, QtCore.Qt.UserRole)
    node.appendRow(item)