import os
import json
import sqlite3
from sqlite3 import Connection

from PyQt5.QtCore import QObject, pyqtSignal

from qgis.core import Qgis, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsMessageLog
from qgis.utils import spatialite_connect

from .analysis import Analysis, load_analyses
from .sample_frame import SampleFrame, load_sample_frames
from .layer import Layer, load_layers, update_layer
from .protocol import Protocol, load as load_protocols, update_protocol
from .raster import Raster, load_rasters
from .event import Event, load as load_events
from .planning_container import PlanningContainer, load as load_planning_containers
from .event_layer import EventLayer
from .metric import Metric, load_metrics, insert_metric, update_metric
from .pour_point import PourPoint, load_pour_points
from .scratch_vector import ScratchVector, load_scratch_vectors
from .stream_gage import StreamGage, load_stream_gages
from .profile import Profile, load_profiles
from .cross_sections import CrossSections, load_cross_sections
from .attachment import Attachment, load_attachments
from .units import load_units
from .db_item import DBItem, dict_factory, load_lookup_table
from .db_item_spatial import DBItemSpatial

from ..QRiS.path_utilities import parse_posix_path
from ..QRiS.protocol_parser import load_protocol_definitions
from typing import Generator, Dict

PROJECT_MACHINE_CODE = 'Project'

# all spatial layers
# feature class, layer name, geometry
project_layers = [
    ('aoi_features', 'AOI Features', 'Polygon'), # Keep so the migration scripts can run
    ('mask_features', 'Mask Features', 'Polygon'), # Keep so the migration scripts can run
    ('sample_frame_features', 'Sample Frame Features', 'Polygon'),
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point'),
    ('profile_centerlines', 'Centerlines', 'Linestring'),
    ('profile_features', 'Profiles', 'Linestring'),
    ('cross_section_features', 'Cross Sections', 'Linestring'),
    ('valley_bottom_features', 'Valley Bottoms', 'Polygon'), # Keep so the migration scripts can run
    ('dce_points', 'DCE Points', 'Point'),
    ('dce_lines', 'DCE Lines', 'Linestring'),
    ('dce_polygons', 'DCE Polygons', 'Polygon')
]

# migrated layers not to be recreated
migrated_layers = [
    'aoi_features',
    'mask_features',
    'valley_bottom_features'
]

class Project(DBItem, QObject):
    project_changed = pyqtSignal()

    def __init__(self, project_file: str):
        DBItem.__init__(self, 'projects', 1, 'Placeholder')
        QObject.__init__(self)

        self.project_file = parse_posix_path(project_file)
        with sqlite3.connect(self.project_file) as conn:
            conn.row_factory = dict_factory
            curs = conn.cursor()

            curs.execute('SELECT id, name, description, map_guid, metadata, created_on FROM projects LIMIT 1')
            project_row = curs.fetchone()
            self.name: str = project_row['name']
            self.id: int = project_row['id']
            self.description: str = project_row['description']
            self.map_guid: str = project_row['map_guid']
            metadata: dict = json.loads(project_row['metadata'] if project_row['metadata'] is not None else '{}')
            self.created_on: str = project_row['created_on']
            self.set_metadata(metadata)

            # get list of lookup tables
            lkp_tables = [row['name'] for row in curs.execute('SELECT DISTINCT name FROM lookups').fetchall()]
            self.lookup_tables = {table: load_lookup_table(curs, table) for table in lkp_tables}

            self.aois = load_sample_frames(curs, sample_frame_type=SampleFrame.AOI_SAMPLE_FRAME_TYPE)
            self.sample_frames = load_sample_frames(curs)
            self.layers = load_layers(curs)
            self.protocols = load_protocols(curs, self.layers)
            self.rasters= load_rasters(curs)
            self.scratch_vectors = load_scratch_vectors(curs, self.project_file)
            self.events = load_events(curs, self.protocols, None, self.layers, self.lookup_tables, self.rasters)
            self.planning_containers = load_planning_containers(curs, self.events)
            self.metrics = load_metrics(curs)
            self.pour_points = load_pour_points(curs)
            self.stream_gages = load_stream_gages(curs)
            self.profiles = load_profiles(curs)
            self.cross_sections = load_cross_sections(curs)
            self.valley_bottoms = load_sample_frames(curs, sample_frame_type=SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE)
            self.analyses = load_analyses(curs, self.analysis_masks(), self.metrics)
            self.attachments = load_attachments(curs)

            self.units = load_units(curs)
        
        # attempt to update protocols 
        try:
            current_protocols = load_protocol_definitions(os.path.dirname(self.project_file), show_experimental=True, show_deprecated=True)
            if current_protocols:
                for current_protocol in current_protocols:
                    if current_protocol.machine_code in [protocol.machine_code for protocol in self.protocols.values()]:
                        updated = False
                        protocol_id = [protocol.id for protocol in self.protocols.values() if protocol.machine_code == current_protocol.machine_code][0]
                        # update existing protocol
                        new_metadata = update_protocol(self.project_file, protocol_id, current_protocol)
                        
                        # Update in-memory object
                        protocol_obj = self.protocols[protocol_id]
                        protocol_obj.name = current_protocol.label
                        protocol_obj.description = current_protocol.description
                        protocol_obj.version = current_protocol.version
                        protocol_obj.set_metadata(new_metadata)

                        # Update layer fields (value_required only)
                        for layer_def in current_protocol.layers:
                            # Find matching layer by machine code (layer_id) and version within the current protocol
                            existing_layer = None
                            for l in protocol_obj.protocol_layers.values():
                                if l.layer_id == layer_def.id:
                                    if str(l.layer_version) == str(layer_def.version):
                                        existing_layer = l
                                        break
                                    # Try float comparison if strings don't match exactly (e.g. "1.0" vs "1")
                                    try:
                                        if float(l.layer_version) == float(layer_def.version):
                                            existing_layer = l
                                            break
                                    except ValueError:
                                        pass

                            if existing_layer:
                                # Check if update is needed before calling update_layer
                                update_needed = False
                                
                                # Check core properties
                                if existing_layer.name != layer_def.label: update_needed = True
                                if existing_layer.qml != layer_def.symbology: update_needed = True
                                if existing_layer.description != layer_def.description: update_needed = True
                                
                                # Check Metadata properties
                                existing_hierarchy = existing_layer.metadata.get('hierarchy', [])
                                new_hierarchy = layer_def.hierarchy if layer_def.hierarchy is not None else []
                                if existing_hierarchy != new_hierarchy: update_needed = True
                                
                                existing_menu_items = existing_layer.metadata.get('menu_items', [])
                                new_menu_items = layer_def.menu_items if layer_def.menu_items is not None else []
                                if existing_menu_items != new_menu_items: update_needed = True

                                if not update_needed and existing_layer.fields:
                                    for field_def in layer_def.fields:
                                        for existing_field in existing_layer.fields:
                                            if existing_field['id'] == field_def.id:
                                                # Check if value_required has changed
                                                if existing_field.get('value_required', False) != field_def.required:
                                                    update_needed = True
                                                    break
                                                
                                                # Check if min/max/precision has changed
                                                if existing_field.get('min') != field_def.min:
                                                    update_needed = True
                                                    break
                                                if existing_field.get('max') != field_def.max:
                                                    update_needed = True
                                                    break
                                                if existing_field.get('precision') != field_def.precision:
                                                    update_needed = True
                                                    break

                                        if update_needed:
                                            break
                                
                                if update_needed:
                                    if update_layer(self.project_file, existing_layer.id, layer_def):
                                         QgsMessageLog.logMessage(f"Updated fields/properties for layer '{existing_layer.name}'", "QRiS", Qgis.Info)
                                         
                                         # Update in-memory layer object properties
                                         existing_layer.name = layer_def.label
                                         existing_layer.qml = layer_def.symbology
                                         existing_layer.description = layer_def.description
                                         
                                         # Update in-memory metadata
                                         if layer_def.hierarchy:
                                             existing_layer.metadata['hierarchy'] = layer_def.hierarchy
                                         elif 'hierarchy' in existing_layer.metadata:
                                             del existing_layer.metadata['hierarchy']
                                             
                                         if layer_def.menu_items:
                                             existing_layer.metadata['menu_items'] = layer_def.menu_items
                                         elif 'menu_items' in existing_layer.metadata:
                                             del existing_layer.metadata['menu_items']
                                         
                                         # Also update the in-memory layer fields
                                         for field_def in layer_def.fields:
                                            for existing_field in existing_layer.fields:
                                                if existing_field['id'] == field_def.id:
                                                    existing_field['value_required'] = field_def.required
                                                    
                                                    # Update keys handling removal if None
                                                    for key, val in [('min', field_def.min), ('max', field_def.max), ('precision', field_def.precision)]:
                                                        if val is not None:
                                                            existing_field[key] = val
                                                        elif key in existing_field:
                                                            del existing_field[key]
                                                            
                                         # Ensure metadata dict is also sync'd (though it should be by reference)
                                         existing_layer.metadata['fields'] = existing_layer.fields

                        # metrics
                        for metric in current_protocol.metrics:
                            key_tuple = (metric.id, metric.version, current_protocol.machine_code)
                            existing_metrics = [
                                m for m in self.metrics.values()
                                if (m.machine_name, m.version, m.protocol_machine_code) == key_tuple
                            ]
                            if not existing_metrics:
                                metric_metadata = {}
                                if metric.minimum_value is not None:
                                    metric_metadata['minimum_value'] = metric.minimum_value
                                if metric.maximum_value is not None:
                                    metric_metadata['maximum_value'] = metric.maximum_value
                                if metric.precision is not None:
                                    metric_metadata['precision'] = metric.precision
                                if metric.status is not None:
                                    metric_metadata['status'] = metric.status
                                if metric.hierarchy is not None:
                                    metric_metadata['hierarchy'] = metric.hierarchy

                                metric_id, metric_obj = insert_metric(
                                    self.project_file, metric.label, metric.id, current_protocol.machine_code,
                                    metric.description, metric.default_level, metric.calculation_machine_code,
                                    metric.parameters, None, metric.definition_url, metric_metadata, metric.version
                                )
                                self.metrics[metric_id] = metric_obj
                                QgsMessageLog.logMessage(
                                    f"Metric '{metric.label}' (ID: {metric.id}, Version: {metric.version}) added to protocol '{current_protocol.machine_code}'.","QRiS", Qgis.Info)
                            else:
                                existing_metric: Metric = existing_metrics[0]
                                # Only update label, description, and metadata if changed
                                update_needed = False
                                new_label = metric.label if hasattr(metric, 'label') else existing_metric.name
                                new_description = metric.description if hasattr(metric, 'description') else existing_metric.description
                                new_status = metric.status if hasattr(metric, 'status') else existing_metric.status
                                new_definition_url = metric.definition_url if hasattr(metric, 'definition_url') else existing_metric.definition_url
                                # Start with a copy of the existing metadata
                                new_metadata = dict(existing_metric.metadata) if existing_metric.metadata else {}
                                # List of protocol attributes to check and update in metadata
                                protocol_attrs = [
                                    ('minimum_value', getattr(metric, 'minimum_value', None)),
                                    ('maximum_value', getattr(metric, 'maximum_value', None)),
                                    ('precision', getattr(metric, 'precision', None)),
                                    ('tolerance', getattr(metric, 'tolerance', None)),
                                    ('status', new_status),
                                    ('hierarchy', getattr(metric, 'hierarchy', None)),
                                ]
                                for key, value in protocol_attrs:
                                    if value is not None:
                                        if key not in new_metadata or new_metadata.get(key) != value:
                                            new_metadata[key] = value
                                            update_needed = True
                                # Compare label
                                if existing_metric.name != new_label:
                                    update_needed = True
                                # Compare description
                                if existing_metric.description != new_description:
                                    update_needed = True
                                # Compare definition_url
                                if existing_metric.definition_url != new_definition_url:
                                    update_needed = True
                                # Only update if metric_function and metric_params are unchanged
                                if (existing_metric.metric_function == metric.calculation_machine_code and
                                    existing_metric.metric_params == metric.parameters and
                                    update_needed):
                                    updated_metric = update_metric(
                                        self.project_file,
                                        existing_metric.id,
                                        new_label,
                                        existing_metric.machine_name,
                                        existing_metric.protocol_machine_code,
                                        new_description,
                                        metric.default_level,
                                        existing_metric.metric_function,
                                        existing_metric.metric_params,
                                        None,
                                        new_definition_url,
                                        new_metadata,
                                        existing_metric.version
                                    )
                                    self.metrics[existing_metric.id] = updated_metric
                                    updated = True
                                    QgsMessageLog.logMessage(
                                        f"Metric '{existing_metric.name}' (ID: {existing_metric.machine_name}, Version: {existing_metric.version}) label/description/metadata/status/definition_url updated in protocol '{current_protocol.machine_code}'.",
                                        "QRiS", Qgis.Info
                                    )
                        if updated == True:
                            QgsMessageLog.logMessage(f"Protocol '{current_protocol.machine_code}' updated.", "QRiS", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f'Error updating protocols: {e}', 'QRiS', Qgis.Warning)
        

    def analysis_masks(self) -> Dict[int, SampleFrame]:
        masks = self.sample_frames.copy()
        masks.update(self.aois)
        masks.update(self.valley_bottoms)
        return masks

    def get_relative_path(self, absolute_path: str) -> str:
        return parse_posix_path(os.path.relpath(absolute_path, os.path.dirname(self.project_file)))

    def get_absolute_path(self, relative_path: str) -> str:
        return parse_posix_path(os.path.join(os.path.dirname(self.project_file), relative_path))

    def get_safe_file_name(self, raw_name: str, ext: str = None) -> str:
        name = raw_name.strip().replace(' ', '_').replace('__', '_')
        if ext is not None:
            name = name + ext
        return name

    def add_db_item(self, db_item) -> None:
        """Add a new DBItem to the project and generate its spatial view if applicable."""
        if isinstance(db_item, SampleFrame):
            if db_item.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                self.aois[db_item.id] = db_item
            elif db_item.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                self.valley_bottoms[db_item.id] = db_item
            else:
                self.sample_frames[db_item.id] = db_item
        elif isinstance(db_item, PourPoint):
            self.pour_points[db_item.id] = db_item
        elif isinstance(db_item, ScratchVector):
            self.scratch_vectors[db_item.id] = db_item
        elif isinstance(db_item, Raster):
            self.rasters[db_item.id] = db_item
        elif isinstance(db_item, Event):
            self.events[db_item.id] = db_item
        elif isinstance(db_item, Analysis):
            self.analyses[db_item.id] = db_item
        elif isinstance(db_item, Profile):
            self.profiles[db_item.id] = db_item
        elif isinstance(db_item, CrossSections):
            self.cross_sections[db_item.id] = db_item
        elif isinstance(db_item, PlanningContainer):
            self.planning_containers[db_item.id] = db_item
        elif isinstance(db_item, Attachment):
            self.attachments[db_item.id] = db_item
        else:
            raise TypeError(f"Unsupported db_item type: {type(db_item)}")
    
        self.project_changed.emit()

    def remove(self, db_item: DBItem) -> None:
        """Remove a DBItem from the project."""
        if isinstance(db_item, DBItemSpatial):
            with sqlite3.connect(self.project_file) as conn:
                curs = conn.cursor()
                db_item.drop_spatial_view(curs)
                conn.commit()
        if isinstance(db_item, SampleFrame):
            if db_item.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                self.aois.pop(db_item.id)
            elif db_item.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                self.valley_bottoms.pop(db_item.id)
            else:
                self.sample_frames.pop(db_item.id)
        elif isinstance(db_item, Raster):
            self.rasters.pop(db_item.id)
        elif isinstance(db_item, Event):
            self.events.pop(db_item.id)
        elif isinstance(db_item, PourPoint):
            self.pour_points.pop(db_item.id)
        elif isinstance(db_item, Analysis):
            self.analyses.pop(db_item.id)
        elif isinstance(db_item, ScratchVector):
            self.scratch_vectors.pop(db_item.id)
        elif isinstance(db_item, Profile):
            self.profiles.pop(db_item.id)
        elif isinstance(db_item, CrossSections):
            self.cross_sections.pop(db_item.id)
        elif isinstance(db_item, EventLayer):
            db_item.delete_event_layer_features(self.project_file)
            event_layer_index = list(event_layer.id for event_layer in self.events[db_item.event_id].event_layers).index(db_item.id)
            self.events[db_item.event_id].event_layers.pop(event_layer_index)
        elif isinstance(db_item, PlanningContainer):
            self.planning_containers.pop(db_item.id)
        elif isinstance(db_item, Attachment):
            self.attachments.pop(db_item.id)
        else:
            raise Exception('Attempting to remove unhandled database type from project')
        self.project_changed.emit()

    def update_metadata(self, metadata: dict = None):

        if metadata is not None:
            self.metadata.update(metadata)

        with sqlite3.connect(self.project_file) as conn:
            conn.execute('UPDATE projects SET metadata = ? WHERE id = ?', [json.dumps(self.metadata), self.id])

        self.project_changed.emit()

    def scratch_rasters(self) -> Dict[int, Raster]:
        """ Returns a dictionary of all project rasters EXCEPT basemaps"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is True}

    def surface_rasters(self) -> Dict[int, Raster]:
        """ Returns a dictionary of all project surface rasters"""

        return {id: raster for id, raster in self.rasters.items() if raster.is_context is False}

    def get_vector_dbitems(self) -> Generator[DBItemSpatial, None, None]:

        # yield all vector dbitems
        for dbitem in self.aois.values():
            yield dbitem
        for dbitem in self.sample_frames.values():
            yield dbitem
        for dbitem in self.pour_points.values():
            yield dbitem
        for dbitem in self.stream_gages.values():
            yield dbitem
        for dbitem in self.profiles.values():
            yield dbitem
        for dbitem in self.cross_sections.values():
            yield dbitem
        for dbitem in self.scratch_vectors.values():
            yield dbitem
        for dbitem in self.valley_bottoms.values():
            yield dbitem
        # for dbitem in self.layers.values():
        #     yield dbitem

    def refresh_spatial_views(self) -> None:
        """Recreate all spatial views in the project."""
        try:
            with sqlite3.connect(self.project_file) as conn:
                curs = conn.cursor()
                for dbitem in self.get_vector_dbitems():
                    if not isinstance(dbitem, DBItemSpatial):
                        continue
                    dbitem.create_spatial_view(curs)
                    if isinstance(dbitem, PourPoint):
                        dbitem.catchment.create_spatial_view(curs)
                for analysis in self.analyses.values():
                    analysis.create_spatial_view(curs)
                for event in self.events.values():
                    for event_layer in event.event_layers:
                        event_layer.create_spatial_view(curs)
                conn.commit()
        except Exception as ex:
            conn.rollback()
            raise Exception(f"Error refreshing spatial views: {ex}") from ex


def create_geopackage_table(geometry_type: str, table_name: str, geopackage_path: str, full_path: str, field_tuple_list: list = None):
    """
        Creates tables in existing or new geopackages
        geometry_type (string):  NoGeometry, Polygon, Linestring, Point, etc...
        table_name (string): Name for the new table
        geopackage_path (string): full path to the geopackage i.e., dir/package.gpkg
        full_path (string): full path including the layer i.e., dir/package.gpkg|layername=layer
        field_tuple_list (list): a list of tuples as field name and QVariant field types i.e., [('my_field', QVarient.Double)]
        """
    memory_layer = QgsVectorLayer(geometry_type, "memory_layer", "memory")
    if field_tuple_list:
        fields = []
        for field_tuple in field_tuple_list:
            field = QgsField(field_tuple[0], field_tuple[1])
            fields.append(field)
        memory_layer.dataProvider().addAttributes(fields)
        memory_layer.updateFields()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = table_name
    options.driverName = 'GPKG'
    transform = QgsCoordinateTransformContext()
    if os.path.exists(geopackage_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormatV3(memory_layer, geopackage_path, transform, options)


def apply_db_migrations(db_path: str):
    conn: Connection = spatialite_connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.execute('SELECT EnableGpkgMode();')
    curs = conn.cursor()

    existing_layers = [layer[0] for layer in curs.execute('SELECT table_name, data_type FROM gpkg_contents WHERE data_type = "features"').fetchall()]
    existing_layers = existing_layers + migrated_layers

    for fc_name, layer_name, geometry_type in project_layers:
        if fc_name not in existing_layers:
            features_path = '{}|layername={}'.format(db_path, layer_name)
            create_geopackage_table(geometry_type, fc_name, db_path, features_path, None)
            yield f'Applying QRiS Database Migrations: create feature class {layer_name}'

    try:
        curs.execute('SELECT name FROM sqlite_master WHERE type="view"')
        views = curs.fetchall()
        for view in views:
            view_name = view[0]
            if view_name.startswith('vw_aoi') or view_name.startswith('vw_valley_bottom'):
                curs.execute(f'PRAGMA table_info({view_name})')
                columns = curs.fetchall()
                mask_column_name = 'mask_id' if view_name.startswith('vw_aoi') else 'valley_bottom_id'
                mask_id_column = next((column for column in columns if column[1] == mask_column_name), None)
                if mask_id_column is not None:
                    mask_id = curs.execute(f'SELECT {mask_column_name} FROM {view_name} LIMIT 1').fetchone()
                    if mask_id is not None:
                        conn.execute('BEGIN')
                        curs.execute(f'DROP VIEW IF EXISTS {view_name}')
                        curs.execute(f'CREATE VIEW {view_name} AS SELECT * FROM sample_frame_features WHERE sample_frame_id = {mask_id[0]}') 
                        yield f'Applying QRiS Database Migrations: updated view {view_name}'
                        conn.commit()
    except Exception as ex:
        conn.rollback()
        raise ex

    try:
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'db', 'migrations')
        migration_files = os.listdir(migrations_dir)
        sorted_migration_files = sorted(migration_files)
        for migration_file in sorted_migration_files:
            curs.execute('SELECT * FROM migrations WHERE file_name LIKE ?', [migration_file])
            migration_row = curs.fetchone()
            if migration_row is None:
                try:
                    migration_path = os.path.join(migrations_dir, migration_file)
                    yield f'Applying QRiS Database Migrations: {migration_file}'
                    with open(migration_path, 'r') as f:
                        sql_commands = f.read()
                    conn.execute('BEGIN')
                    curs.executescript(sql_commands)
                    curs.execute('INSERT INTO migrations (file_name) VALUES (?)', [migration_file])
                    conn.commit()
                except Exception as ex:
                    conn.rollback()
                    raise ex
    except Exception as ex:
        conn.rollback()
        raise ex

def test_project(db_path: str) -> bool:
    """ Tests if the given database path is a valid QRiS project database """

    if not os.path.exists(db_path):
        return False

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        curs = conn.cursor()
        # check if the project table exists
        curs.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="projects"')
        if curs.fetchone() is None:
            return False
    return True

