import os
import json
import shutil
import sqlite3

from osgeo import ogr

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsVectorLayer, QgsMessageLog
from qgis.utils import iface
from qgis.PyQt.QtCore import QSettings

try:
    import rsxml
    QgsMessageLog.logMessage('rsxml imported from system', 'Riverscapes Viewer', Qgis.Info)
except ImportError:
    QgsMessageLog.logMessage('rsxml not found in system, importing from source', 'Riverscapes Viewer', Qgis.Info)
    rsxml = None

from ...__version__ import __version__ as qris_version
from ..model.event import Event, EVENT_TYPE_LOOKUP
from ..model.analysis import Analysis
from ..model.profile import Profile
from ..model.pour_point import PourPoint
from ..model.cross_sections import CrossSections
from ..model.project import Project as QRiSProject
from ..model.raster import Raster
from ..model.scratch_vector import ScratchVector, scratch_gpkg_path
from ..model.stream_gage import StreamGage
from ..model.sample_frame import SampleFrame

from .utilities import add_standard_form_buttons, message_box

# Puting these here for now to avoid circular imports - source: qris_toolbar.py
ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'

PROJECT_MACHINE_NAME = 'RiverscapesStudio'
DEFAULT_EXPORT_PATH = 'default_export_path'


def rsxml_check():
    """ Check if rsxml is available and return True if it is, otherwise show a message box and return False.

    Returns:
        _type_: _description_
    """
    if rsxml is None:
        message_box("Error", "rsxml module is not available. Please install rsxml to export to Riverscapes Studio.")
        return
    False
    return True


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
        self.set_output_path()

        # populate the AOI combo box with aoi names
        for aoi_id, aoi in self.qris_project.aois.items():
            self.cbo_project_bounds_aoi.addItem(aoi.name, aoi_id)

        # Inputs
        inputs_node = QtGui.QStandardItem("Inputs")
        inputs_node.setCheckable(True)
        inputs_node.setCheckState(QtCore.Qt.PartiallyChecked)

        # Riverscapes Node
        riverscapes_node = QtGui.QStandardItem("Riverscapes")
        riverscapes_node.setCheckable(True)
        riverscapes_node.setCheckState(QtCore.Qt.Checked)
        for valley_bottom in self.qris_project.valley_bottoms.values():
            item = QtGui.QStandardItem(valley_bottom.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(valley_bottom, QtCore.Qt.UserRole)
            riverscapes_node.appendRow(item)
        inputs_node.appendRow(riverscapes_node)

        # AOIs
        aois_node = QtGui.QStandardItem("AOIs")
        aois_node.setCheckable(True)
        aois_node.setCheckState(QtCore.Qt.Checked)
        for aoi in self.qris_project.aois.values():
            item = QtGui.QStandardItem(aoi.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(aoi, QtCore.Qt.UserRole)
            aois_node.appendRow(item)
        inputs_node.appendRow(aois_node)

        # Sample Frames
        sample_frames_node = QtGui.QStandardItem("Sample Frames")
        sample_frames_node.setCheckable(True)
        sample_frames_node.setCheckState(QtCore.Qt.Checked)
        for sample_frame in self.qris_project.sample_frames.values():
            item = QtGui.QStandardItem(sample_frame.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(sample_frame, QtCore.Qt.UserRole)
            sample_frames_node.appendRow(item)
        inputs_node.appendRow(sample_frames_node)

        # Profiles
        profiles_node = QtGui.QStandardItem("Profiles")
        profiles_node.setCheckable(True)
        profiles_node.setCheckState(QtCore.Qt.Checked)
        for profile in self.qris_project.profiles.values():
            item = QtGui.QStandardItem(profile.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(profile, QtCore.Qt.UserRole)
            profiles_node.appendRow(item)
        inputs_node.appendRow(profiles_node)

        # Cross Sections
        xsections_node = QtGui.QStandardItem("Cross Sections")
        xsections_node.setCheckable(True)
        xsections_node.setCheckState(QtCore.Qt.Checked)
        for xsection in self.qris_project.cross_sections.values():
            item = QtGui.QStandardItem(xsection.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(xsection, QtCore.Qt.UserRole)
            xsections_node.appendRow(item)
        inputs_node.appendRow(xsections_node)

        # Surfaces
        surfaces_node = QtGui.QStandardItem("Surfaces")
        surfaces_node.setCheckable(True)
        for surface in self.qris_project.rasters.values():
            if surface.is_context:
                continue
            item = QtGui.QStandardItem(surface.name)
            item.setCheckable(True)
            item.setData(surface, QtCore.Qt.UserRole)
            surfaces_node.appendRow(item)
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
            item = QtGui.QStandardItem(pour_point.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(pour_point, QtCore.Qt.UserRole)
            pour_points_node.appendRow(item)
        context_node.appendRow(pour_points_node)

        for context_vector in self.qris_project.scratch_vectors.values():
            item = QtGui.QStandardItem(context_vector.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(context_vector, QtCore.Qt.UserRole)
            context_node.appendRow(item)
        for context in self.qris_project.rasters.values():
            if not context.is_context:
                continue
            item = QtGui.QStandardItem(context.name)
            item.setCheckable(True)
            item.setData(context, QtCore.Qt.UserRole)
            context_node.appendRow(item)
        inputs_node.appendRow(context_node)

        # DCE and Designs
        events_node = QtGui.QStandardItem("Data Capture Events")
        events_node.setCheckable(True)
        events_node.setCheckState(QtCore.Qt.Checked)
        for event in self.qris_project.events.values():
            item = QtGui.QStandardItem(event.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(event, QtCore.Qt.UserRole)
            events_node.appendRow(item)
        self.export_layers_model.appendRow(events_node)

        # Analysis
        analyses_node = QtGui.QStandardItem("Analyses")
        analyses_node.setCheckable(True)
        analyses_node.setCheckState(QtCore.Qt.Checked)
        for analysis in self.qris_project.analyses.values():
            item = QtGui.QStandardItem(analysis.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(analysis, QtCore.Qt.UserRole)
            analyses_node.appendRow(item)
        self.export_layers_model.appendRow(analyses_node)

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

        if self.chk_apply_name_to_output.isChecked():
            name = self.txt_rs_name.text().replace(" ", "_").replace(".", "_").replace(",", "_").replace(";", "_").replace(":", "_").replace("/", "_").replace("\\", "_").replace("?", "_").replace("!", "_").replace("'", "_").replace('"',
                                                                                                                                                                                                                                        "_").replace("<", "_").replace(">", "_").replace("|", "_").replace("*", "_").replace("(", "_").replace(")", "_").replace("[", "_").replace("]", "_").replace("{", "_").replace("}", "_")

        outpath = os.path.join(self.base_folder, name)
        self.txt_outpath.setText(outpath)

    def accept(self) -> None:

        # check if rsxml is available. If not show a message box and return
        if not rsxml_check():
            return

        if self.txt_rs_name.text() == "":
            message_box("Project Name", "Please enter a name for the Riverscapes project.")
            return

        if self.txt_outpath.text() == "":
            message_box("Output Path", "Please select an output path for the Riverscapes project.")
            return

        # make sure the start of the output path is a valid drive letter
        if not os.path.exists(self.txt_outpath.text()[0:2]):
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

        if self.opt_project_bounds_aoi.isChecked():
            # if Select AOI is selected, then warn the user to select an AOI
            if self.cbo_project_bounds_aoi.currentIndex() == 0:
                message_box("Select an AOI", "Please select an AOI or select 'Use all QRiS layers.'")
                return
        if self.rdo_existing.isChecked():
            if self.txt_existing_path.text() == "":
                message_box("Select Existing Project", "Please select an existing QRiS Riverscapes project file (.rs.xml).")
                return
            rs_project_existing = rsxml.project_xml.Project.load_project(self.txt_existing_path.text())
            if rs_project_existing is None:
                message_box("Invalid Existing Project", "The existing project file does not exist or is not a valid Riverscapes project file.")
                return
            if rs_project_existing.project_type != PROJECT_MACHINE_NAME:
                message_box("Wrong Project Type", "The existing project file is not a Riverscapes Studio project.")
                return
            if rs_project_existing.warehouse is None:
                message_box("Missing Warehouse", "The selected project file does was not previously uploaded to the Data Exchange.")
                return

        # create a new project folder if it doesn't exist
        if not os.path.exists(self.txt_outpath.text()):
            os.makedirs(self.txt_outpath.text())

        # copy the geopackage layers to the new project folder
        out_name = 'qris.gpkg'  # os.path.split(self.qris_project.project_file)[1]
        out_geopackage = os.path.abspath(os.path.join(self.txt_outpath.text(), out_name).replace("\\", "/"))

        # Refrfesh the map canvas to ensure all layers are flushed to disk before copying
        iface.mapCanvas().refreshAllLayers()

        shutil.copy(self.qris_project.project_file, out_geopackage)

        # Project Bounds
        if self.opt_project_bounds_all.isChecked():
            # get the extent of all layers
            envelope = None
            for layer in ['dce_points', 'dce_lines', 'dce_polygons']:  # self.qris_project.layers.values():
                geom = None
                lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername={layer}', layer, "ogr")
                for f in lyr.getFeatures():
                    feature_geom = f.geometry()
                    if feature_geom.isNull() or feature_geom.isEmpty():
                        QgsMessageLog.logMessage(f"Feature {f.id()} in layer {layer} has no geometry", 'QRiS', Qgis.Warning)
                        continue
                    if geom is None:
                        geom = f.geometry()
                    else:
                        geom = geom.combine(f.geometry())
                if geom is None or geom.isNull() or geom.isEmpty():
                    continue
                hull = geom.convexHull()
                if envelope is None:
                    envelope = hull
                else:
                    envelope = envelope.combine(hull)

            for layer in self.qris_project.get_vector_dbitems():
                geom = None
                if isinstance(layer, PourPoint):
                    fc_name = 'catchments'
                    id_field = 'pour_point_id'
                elif isinstance(layer, ScratchVector):
                    continue
                elif isinstance(layer, StreamGage):
                    continue
                else:
                    fc_name = layer.fc_name
                    id_field = layer.fc_id_column_name
                lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername={fc_name}', layer.name, "ogr")
                if id_field is not None:
                    lyr.setSubsetString(f"{id_field} = {layer.id}")
                for f in lyr.getFeatures():
                    feature_geom = f.geometry()
                    if feature_geom.isNull() or feature_geom.isEmpty():
                        QgsMessageLog.logMessage(f"Feature {f.id()} in layer {layer} has no geometry", 'QRiS', Qgis.Warning)
                        continue
                    if geom is None:
                        geom = feature_geom
                    else:
                        geom = geom.combine(feature_geom)
                if geom is None or geom.isNull() or geom.isEmpty():
                    continue
                hull = geom.convexHull()
                if envelope is None:
                    envelope = hull
                else:
                    envelope = envelope.combine(hull)

        else:
            # get the extent of the selected AOI
            aoi_id = self.cbo_project_bounds_aoi.currentData()
            aoi: SampleFrame = self.qris_project.aois[aoi_id]
            lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername=sample_frame_features', aoi.name, "ogr")
            lyr.setSubsetString(f"sample_frame_id = {aoi.id}")
            envelope = lyr.getFeatures().__next__().geometry()

        if envelope is not None and not envelope.isNull() and not envelope.isEmpty():
            envelope_hull = envelope.convexHull()
            # check if the envelope is empty or null, or not a polygon type
            if envelope_hull.isEmpty() or envelope_hull.isNull() or envelope_hull.wkbType() not in [ogr.wkbPolygon, ogr.wkbMultiPolygon]:
                QMessageBox.warning(self, "Project Bounds", "Unable to determine project bounds. Please select a different AOI or there are enough layer geometries in the project to produce a polygon project bounds.")
                return
            extent = envelope_hull.boundingBox()
            centroid = envelope_hull.centroid().asPoint()
            geojson = envelope_hull.asJson()
            # write to file
            geojson_filename = "project_bounds.geojson"
            geojson_path = os.path.abspath(os.path.join(self.txt_outpath.text(), geojson_filename).replace("\\", "/"))
            with open(geojson_path, 'w') as f:
                f.write(geojson)

            project_bounds = rsxml.project_xml.ProjectBounds(centroid=rsxml.project_xml.Coords(centroid.x(), centroid.y()),
                                                 bounding_box=rsxml.project_xml.BoundingBox(minLat=extent.yMinimum(),
                                                                                minLng=extent.xMinimum(),
                                                                                maxLat=extent.yMaximum(),
                                                                                maxLng=extent.xMaximum()),
                                                 filepath=geojson_filename)
        else:
            project_bounds = None
            QMessageBox.warning(self, "Project Bounds", "Unable to determine project bounds. Project will still be created but without bounds.")

        xml_path = os.path.abspath(os.path.join(self.txt_outpath.text(), "project.rs.xml").replace("\\", "/"))

        metadata_values = [rsxml.project_xml.Meta('QRiS Project Name', self.qris_project.name),
                           rsxml.project_xml.Meta('QRiS Project Description', self.qris_project.description),
                           rsxml.project_xml.Meta('ModelVersion', '1')]

        for key, value in self.qris_project.metadata.items():
            # if tags are empty, skip
            if key == "tags":
                continue
            if value == "":
                continue
            if key == "metadata":
                dict_metadata = value
                for k, v in dict_metadata.items():
                    metadata_values.append(rsxml.project_xml.Meta(k, v))
            else:
                metadata_values.append(rsxml.project_xml.Meta(key, value))

        warehouse = None
        if self.rdo_existing.isChecked():
            rs_project_existing = rsxml.project_xml.Project.load_project(self.txt_existing_path.text())
            warehouse = rs_project_existing.warehouse

        self.rs_project = rsxml.project_xml.Project(name=self.txt_rs_name.text(),
                                        proj_path=xml_path,
                                        project_type=PROJECT_MACHINE_NAME,
                                        meta_data=rsxml.project_xml.MetaData(values=metadata_values),
                                        warehouse=warehouse,
                                        description=self.txt_description.toPlainText(),
                                        bounds=project_bounds)

        date_created = QtCore.QDateTime.currentDateTime()

        keep_layers: dict = {}  # {layer_name: {id_field: id_field_name, id_values: [id_values]}}

        # Inputs
        input_layers = []
        inputs_node = self.export_layers_model.findItems("Inputs")[0]

        # Surface Rasters
        raster_datasets = []
        raster_node = self.find_child_node(inputs_node, "Surfaces")
        if raster_node:
            for i in range(raster_node.rowCount()):
                raster_item = raster_node.child(i)
                if raster_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                raster: Raster = raster_item.data(QtCore.Qt.UserRole)

                # check if raster is surface or context
                if raster.is_context:
                    raster_xml_id = f'context_{raster.id}'
                else:
                    raster_xml_id = f'surface_{raster.id}'

                if 'rasters' not in keep_layers:
                    keep_layers['rasters'] = {'id_field': 'id', 'id_values': []}
                keep_layers['rasters']['id_values'].append(str(raster.id))

                src_raster_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), raster.path).replace("\\", "/"))
                out_raster_path = os.path.abspath(os.path.join(self.txt_outpath.text(), raster.path).replace("\\", "/"))
                if not os.path.exists(os.path.dirname(out_raster_path)):
                    os.makedirs(os.path.dirname(out_raster_path))
                shutil.copy(src_raster_path, out_raster_path)

                raster_datasets.append(rsxml.project_xml.Dataset(xml_id=raster_xml_id,
                                                     name=raster.name,
                                                     path=raster.path,
                                                     ds_type='Raster'))

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

                view_name = f'vw_valley_bottom_{valley_bottom.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name='sample_frame_features',
                                         field_name='sample_frame_id',
                                         id_value=valley_bottom.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='POLYGON')

                input_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                          name=valley_bottom.name,
                                                          ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                          lyr_type='valley_bottom'))

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

                view_name = f'vw_aoi_{aoi.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name='sample_frame_features',
                                         field_name='sample_frame_id',
                                         id_value=aoi.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='POLYGON')

                input_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                          name=aoi.name,
                                                          ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                          lyr_type='aoi'))

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

                view_name = f'vw_sample_frame_{sample_frame.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name='sample_frame_features',
                                         field_name='sample_frame_id',
                                         id_value=sample_frame.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='POLYGON')

                input_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                          name=sample_frame.name,
                                                          ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                          lyr_type='sample_frame'))

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

                view_name = f'vw_profile_{profile.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name=profile_fc,
                                         field_name='profile_id',
                                         id_value=profile.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='LINESTRING')

                input_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                          name=profile.name,
                                                          ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                          lyr_type='profile'))

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

                view_name = f'vw_cross_section_{xsection.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name='cross_section_features',
                                         field_name='cross_section_id',
                                         id_value=xsection.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='LINESTRING')

                input_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                          name=xsection.name,
                                                          ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                          lyr_type='cross_section'))

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
                pour_point_layers = []

                if 'pour_points' not in keep_layers:
                    keep_layers['pour_points'] = {'id_field': 'fid', 'id_values': []}
                keep_layers['pour_points']['id_values'].append(str(pour_point.id))

                view_name = f'vw_pour_point_{pour_point.id}'
                self.create_spatial_view(view_name=view_name,
                                         fc_name='pour_points',
                                         field_name='fid',
                                         id_value=pour_point.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='POINT')

                pour_point_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                               name=pour_point.name,
                                                               ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                               lyr_type='pour_points'))

                if 'catchments' not in keep_layers:
                    keep_layers['catchments'] = {'id_field': 'pour_point_id', 'id_values': []}
                keep_layers['catchments']['id_values'].append(str(pour_point.id))

                catchment_view = f'vw_catchment_{pour_point.id}'
                self.create_spatial_view(view_name=catchment_view,
                                         fc_name='catchments',
                                         field_name='pour_point_id',
                                         id_value=pour_point.id,
                                         out_geopackage=out_geopackage,
                                         geom_type='POLYGON')

                pour_point_layers.append(rsxml.project_xml.GeopackageLayer(lyr_name=catchment_view,
                                                               name=pour_point.name,
                                                               ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                               lyr_type='catchments'))

                pour_point_gpkgs.append(rsxml.project_xml.Geopackage(xml_id=f'pour_points_{pour_point.id}_gpkg',
                                                         name=pour_point.name,
                                                         path=out_name,
                                                         layers=pour_point_layers))

        # context vectors
        context_layers = []
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
                # check if raster is surface or context
                if raster.is_context:
                    raster_xml_id = f'context_{raster.id}'
                else:
                    raster_xml_id = f'surface_{raster.id}'

                if 'rasters' not in keep_layers:
                    keep_layers['rasters'] = {'id_field': 'id', 'id_values': []}
                keep_layers['rasters']['id_values'].append(str(raster.id))

                raster_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), raster.path).replace("\\", "/"))
                out_raster_path = os.path.abspath(os.path.join(self.txt_outpath.text(), raster.path).replace("\\", "/"))
                if not os.path.exists(os.path.dirname(out_raster_path)):
                    os.makedirs(os.path.dirname(out_raster_path))
                shutil.copy(raster_path, out_raster_path)

                raster_datasets.append(rsxml.project_xml.Dataset(xml_id=raster_xml_id,
                                                     name=raster.name,
                                                     path=raster.path,
                                                     ds_type='Raster'))
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

                context_layers.append(rsxml.project_xml.GeopackageLayer(summary=f'context_{geom_type.lower()}',
                                                            lyr_name=context_vector.fc_name,
                                                            name=context_vector.name,
                                                            ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                            lyr_type='context'))

        inputs_gpkg = rsxml.project_xml.Geopackage(xml_id=f'inputs_gpkg',
                                       name=f'Inputs',
                                       path=out_name,
                                       layers=input_layers)

        out_gpkgs = [inputs_gpkg]
        if len(context_layers) > 0:
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

            out_gpkgs.append(rsxml.project_xml.Geopackage(xml_id=f'context_gpkg',
                                              name=f'Context',
                                              path='context/feature_classes.gpkg',
                                              layers=context_layers))

        self.rs_project.realizations.append(rsxml.project_xml.Realization(xml_id=f'inputs',
                                                              name='Inputs',
                                                              date_created=date_created.toPyDateTime(),
                                                              product_version=qris_version,
                                                              datasets=raster_datasets + out_gpkgs + pour_point_gpkgs))

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
                if all([layer.feature_count(self.qris_project.project_file) == 0 for layer in event.event_layers]):
                    continue
                event_type = EVENT_TYPE_LOOKUP[event.event_type.id]

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
                photo_datasets = []

                source_photos_dir = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
                photo_dce_folder = os.path.abspath(os.path.join(self.txt_outpath.text(), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
                if os.path.exists(source_photos_dir):
                    shutil.copytree(source_photos_dir, photo_dce_folder)
                    # list photos in the photos folder
                    for photo in os.listdir(photo_dce_folder):
                        photo_metadata = all_photo_metadata[photo]
                        photo_id = os.path.splitext(photo)[0]
                        # get the lat long of the photo
                        photo_meta = rsxml.MetaData(values=[rsxml.Meta('lat', photo_metadata['latitude']),
                                                            rsxml.Meta('long', photo_metadata['longitude']),
                                                            rsxml.Meta('timestamp', photo_metadata['timestamp'])
                                                            ])

                        photo_datasets.append(rsxml.Dataset(xml_id=photo_id,
                                                            name=photo,
                                                            path=f'photos/dce_{str(event.id).zfill(3)}/{photo}',
                                                            meta_data=photo_meta,
                                                            ds_type='Image'))

                meta = rsxml.project_xml.MetaData(values=[rsxml.project_xml.Meta(event_type, "")])
                # prepare the datasets
                geopackage_layers = []
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

                    view_name = f'vw_{layer.layer.layer_id}_{event.id}'

                    layer_fields: list = layer.layer.metadata.get('fields', None)
                    out_fields = '*'
                    if layer_fields is not None and len(layer_fields) > 0:
                        field_names = [field['label'] for field in layer_fields]
                        out_fields = ", ".join([f'json_extract(metadata, \'$.attributes.{field}\') AS "{field}"' for field in field_names])
                    sql = f"CREATE VIEW {view_name} AS SELECT fid, geom, event_id, event_layer_id, {out_fields}, metadata FROM {fc_name} WHERE event_id == {event.id} AND event_layer_id == {layer.layer.id}"
                    self.create_spatial_view(view_name=view_name,
                                             fc_name=fc_name,
                                             field_name='event_id',
                                             id_value=event.id,
                                             out_geopackage=out_geopackage,
                                             geom_type=geom_type.upper(),
                                             sql=sql)

                    gp_lyr = rsxml.project_xml.GeopackageLayer(lyr_name=view_name,
                                                   name=layer.name,
                                                   ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                                   lyr_type=layer.layer.layer_id)
                    geopackage_layers.append(gp_lyr)

                events_gpkg = rsxml.project_xml.Geopackage(xml_id=f'dce_{event.id}_gpkg',
                                               name=f'{event.name}',
                                               path=out_name,
                                               layers=geopackage_layers)

                # # self.rs_project.common_datasets.append(gpkg)
                # ds = [RefDataset(lyr.lyr_name, lyr) for lyr in geopackage_layers]

                realization = rsxml.project_xml.Realization(xml_id=f'realization_qris_{event.id}',
                                                name=event.name,
                                                date_created=date_created.toPyDateTime(),
                                                product_version=qris_version,
                                                datasets=[events_gpkg] + photo_datasets,
                                                meta_data=meta)

                # add description if it exists
                if event.description:
                    realization.description = event.description

                self.rs_project.realizations.append(realization)

        # add analyses
        analysis_nodes = self.export_layers_model.findItems("Analyses")
        if analysis_nodes:
            analysis_node = analysis_nodes[0]
            for i in range(analysis_node.rowCount()):
                analysis_item = analysis_node.child(i)
                if analysis_item.checkState() == QtCore.Qt.Unchecked:
                    continue
                analysis: Analysis = analysis_item.data(QtCore.Qt.UserRole)

                geopackage_layers = []
                # analysis: Analysis = analysis
                sample_frame: SampleFrame = analysis.sample_frame

                # flatten the table of analysis metrics
                analysis_metrics = []
                for metric_id, metric in analysis.analysis_metrics.items():
                    analysis_metrics.append([metric_id, metric.level_id])

                if 'analyses' not in keep_layers:
                    keep_layers['analyses'] = {'id_field': 'analysis_id', 'id_values': []}
                keep_layers['analyses']['id_values'].append(str(analysis.id))
                if 'analysis_metrics' not in keep_layers:
                    keep_layers['analysis_metrics'] = {'id_field': 'analysis_id', 'id_values': []}
                keep_layers['analysis_metrics']['id_values'].append(str(analysis.id))

                # create the analysis view
                analysis_view = f'vw_analysis_{analysis.id}'

                # prepare sql string for each metric
                sql_metric = ", ".join(
                    [f'CASE WHEN metric_id = {metric_id} THEN (CASE WHEN is_manual = 1 THEN manual_value ELSE automated_value END) END AS "{analysis_metric.metric.name}"' for metric_id, analysis_metric in analysis.analysis_metrics.items()])
                sql = f"""CREATE VIEW {analysis_view} AS SELECT * FROM sample_frame_features JOIN (SELECT sample_frame_feature_id, {sql_metric} FROM metric_values JOIN metrics ON metric_values.metric_id == metrics.id WHERE metric_values.analysis_id = {analysis.id} GROUP BY sample_frame_feature_id) AS x ON sample_frame_features.fid = x.sample_frame_feature_id"""
                if sql_metric == '':
                    sql = f"CREATE VIEW {analysis_view} AS SELECT * FROM sample_frame_features WHERE sample_frame_id == {sample_frame.id}"
                self.create_spatial_view(view_name=analysis_view,
                                         fc_name=None,
                                         field_name=None,
                                         id_value=None,
                                         out_geopackage=out_geopackage,
                                         geom_type="POLYGON",
                                         sql=sql)

                gp_lyr = rsxml.project_xml.GeopackageLayer(lyr_name=analysis_view,
                                               name=analysis.name,
                                               ds_type=rsxml.project_xml.GeoPackageDatasetTypes.VECTOR,
                                               lyr_type='analysis')
                geopackage_layers.append(gp_lyr)

                analysis_gpkg = rsxml.project_xml.Geopackage(xml_id=f'{analysis.id}_gpkg',
                                                 name=f'{analysis.name}',
                                                 path=out_name,
                                                 layers=geopackage_layers)

                realization = rsxml.project_xml.Realization(xml_id=f'analysis_{analysis.id}',
                                                name=analysis.name,
                                                date_created=date_created.toPyDateTime(),
                                                product_version=qris_version,
                                                datasets=[analysis_gpkg])
                # meta_data=meta)
                self.rs_project.realizations.append(realization)

        # open the geopackage using ogr
        ds_gpkg: ogr.DataSource = ogr.Open(out_geopackage, 1)
        for layer in ['analyses', 'analysis_metrics', 'catchments', 'cross_sections', 'cross_section_features', 'dce_lines', 'dce_points', 'dce_polygons', 'events', 'event_layers', 'pour_points', 'profile_centerlines', 'profile_features', 'profiles', 'rasters', 'scratch_vectors', 'sample_frame_features', 'sample_frames']:
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

            # unfortunately, event_rasters table does not have an fid column, we need to delete the rows manually
            curs = conn.cursor()
            curs.execute("DELETE FROM event_rasters WHERE event_id NOT IN (SELECT id FROM events)")
            conn.commit()  # Commit the transaction before executing VACUUM

            conn.execute("VACUUM")

        self.rs_project.write()

        return super().accept()

    def find_child_node(self, node: QtWidgets.QTreeWidgetItem, tag: str):

        for i in range(node.rowCount()):
            child = node.child(i)
            if child.text() == tag:
                return child
        return None

    @staticmethod
    def create_spatial_view(view_name: str, fc_name, field_name: str, id_value: int, out_geopackage: str, geom_type: str, epsg: int = 4326, sql: str = None):
        # create spaitail view of the aoi
        sql = sql if sql is not None else f"CREATE VIEW {view_name} AS SELECT * FROM {fc_name} WHERE {field_name} == {id_value}"
        with sqlite3.connect(out_geopackage) as conn:
            curs = conn.cursor()
            # check if the view already exists, if so, delete it
            curs.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view_name}'")
            if curs.fetchone():
                curs.execute(f"DROP VIEW {view_name}")
                curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = '{view_name}'")
                curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = '{view_name}'")

            curs.execute(sql)
            # add view to geopackage
            sql = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id) VALUES (?, ?, ?, ?, ?)"
            curs.execute(sql, [view_name, "features", view_name, "", epsg])
            sql = "INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m) VALUES (?, ?, ?, ?, ?, ?)"
            curs.execute(sql, [view_name, 'geom', geom_type, epsg, 0, 0])
            conn.commit()

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

    def change_project_bounds(self):

        if self.opt_project_bounds_aoi.isChecked():
            self.cbo_project_bounds_aoi.setEnabled(True)
        else:
            self.cbo_project_bounds_aoi.setEnabled(False)

    def set_checkbox_state(self, state: bool):

        for i in range(self.export_layers_model.rowCount()):
            item = self.export_layers_model.item(i)
            item.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    def browse_existing(self):

        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Existing Project', '', 'Riverscapes Project (*.rs.xml)')[0]
        if path:
            self.txt_existing_path.setText(path)

    def change_new_or_existing(self):

        if self.rdo_new.isChecked():
            self.txt_existing_path.setEnabled(False)
            self.btn_existing.setEnabled(False)
            self.lbl_existing.setEnabled(False)
        else:
            self.txt_existing_path.setEnabled(True)
            self.btn_existing.setEnabled(True)
            self.lbl_existing.setEnabled(True)

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

        self.chk_apply_name_to_output = QtWidgets.QCheckBox("Use project name as output folder")
        self.chk_apply_name_to_output.setChecked(True)
        self.chk_apply_name_to_output.clicked.connect(self.set_output_path)
        self.grid.addWidget(self.chk_apply_name_to_output, 1, 1, 1, 1)

        # add label and horizontal layout with textbox and small button for output path
        self.lbl_output = QtWidgets.QLabel("Output Path")
        self.lbl_output.setToolTip("Select the folder where the Riverscapes project will be saved")
        self.grid.addWidget(self.lbl_output, 2, 0, 1, 1)

        self.horiz_output = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_output, 2, 1, 1, 1)

        self.txt_outpath = QtWidgets.QLineEdit()
        self.horiz_output.addWidget(self.txt_outpath)

        self.btn_output = QtWidgets.QPushButton("...")
        self.btn_output.setMaximumWidth(30)
        self.btn_output.clicked.connect(self.browse_path)
        self.horiz_output.addWidget(self.btn_output)

        # Project Bounds
        self.lbl_project_bounds = QtWidgets.QLabel("Project Bounds")
        self.lbl_project_bounds.setToolTip("Select the extent of the project. This is used for display purposes on the Riverscapes Data Exchange")
        self.grid.addWidget(self.lbl_project_bounds, 3, 0, 1, 1, QtCore.Qt.AlignTop)

        self.vert_project_bounds = QtWidgets.QVBoxLayout()
        self.grid.addLayout(self.vert_project_bounds, 3, 1, 1, 1)

        self.opt_project_bounds_all = QtWidgets.QRadioButton("Use all QRiS layers")
        self.opt_project_bounds_all.setToolTip("Use the extent of all QRiS layers in the project")
        self.opt_project_bounds_all.setChecked(True)
        self.opt_project_bounds_all.clicked.connect(self.change_project_bounds)
        self.vert_project_bounds.addWidget(self.opt_project_bounds_all)

        self.horiz_project_bounds_aoi = QtWidgets.QHBoxLayout()
        self.vert_project_bounds.addLayout(self.horiz_project_bounds_aoi)

        self.opt_project_bounds_aoi = QtWidgets.QRadioButton("Use AOI")
        self.opt_project_bounds_aoi.setToolTip("Use the extent of a selected AOI")
        self.opt_project_bounds_aoi.clicked.connect(self.change_project_bounds)
        self.horiz_project_bounds_aoi.addWidget(self.opt_project_bounds_aoi)

        self.cbo_project_bounds_aoi = QtWidgets.QComboBox()
        self.cbo_project_bounds_aoi.addItem("Select AOI")
        self.cbo_project_bounds_aoi.setEnabled(False)
        self.horiz_project_bounds_aoi.addWidget(self.cbo_project_bounds_aoi)

        # New or Existing Project
        self.lbl_new_or_existing = QtWidgets.QLabel("Export Type")
        self.lbl_new_or_existing.setToolTip("Select whether to create a new Riverscapes Studio project or update an existing project")
        self.grid.addWidget(self.lbl_new_or_existing, 4, 0, 1, 1)

        self.group_new_or_existing = QtWidgets.QButtonGroup(self)

        self.rdo_new = QtWidgets.QRadioButton("New Riverscapes Studio Project")
        self.rdo_new.setToolTip("Export as a new Riverscapes Studio project")
        self.group_new_or_existing.addButton(self.rdo_new)
        self.rdo_new.setChecked(True)
        self.rdo_new.clicked.connect(self.change_new_or_existing)
        self.grid.addWidget(self.rdo_new, 4, 1, 1, 1)

        self.rdo_existing = QtWidgets.QRadioButton("Update Existing Riverscapes Studio Project")
        self.rdo_existing.setToolTip("Update a previously uploaded Riverscapes Studio project")
        self.group_new_or_existing.addButton(self.rdo_existing)
        self.rdo_existing.clicked.connect(self.change_new_or_existing)
        self.grid.addWidget(self.rdo_existing, 5, 1, 1, 1)

        self.horiz_existing = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_existing, 6, 1, 1, 1)

        self.lbl_existing = QtWidgets.QLabel("Existing Project rs.xml file")
        self.lbl_existing.setEnabled(False)
        self.horiz_existing.addWidget(self.lbl_existing)

        self.txt_existing_path = QtWidgets.QLineEdit()
        self.txt_existing_path.setReadOnly(True)
        self.txt_existing_path.setEnabled(False)
        self.horiz_existing.addWidget(self.txt_existing_path)

        self.btn_existing = QtWidgets.QPushButton("...")
        self.btn_existing.setMaximumWidth(30)
        self.btn_existing.clicked.connect(self.browse_existing)
        self.btn_existing.setEnabled(False)
        self.horiz_existing.addWidget(self.btn_existing)

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
        self.vert.addLayout(add_standard_form_buttons(self, "metrics"))
