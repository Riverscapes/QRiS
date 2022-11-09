import os
import sqlite3
import shutil
from typing import Dict

from .qris_task import QRiSTask
from .new_project import NewProject
from .xml_builder import XMLBuilder
from .rs_project import RSProject, RSLayer
from ..model.db_item import dict_factory
from .model_config import ModelConfig

cfg = ModelConfig('http://xml.riverscapes.net/Projects/XSD/V1/BRAT.xsd', '__version__')


class EventExportTask(QRiSTask):

    def __init__(self, iface, db_path: str, event_id: int, output_project_name: str, output_path: str, method_id: int, basemap_raster_paths: Dict[int, str]):
        """
        iface: QGIS interface
        db_path: Full absolute path to the QRiS GeoPackage
        event_id: the ID of the event to be exported
        output_project_name: name for the output riverscapes project based on the QRiS DCE.
        output_path: folder where the riverscapes project should be created.
        project_type: String representing the project type that should be used in <ProjectType></ProjectType>
        """

        super().__init__(iface, 'Export Event Task', 'QRiS_EventExportTask')

        self.db_path = db_path
        self.output_project_name = output_project_name
        self.event_id = event_id
        self.output_path = output_path
        self.method_id = method_id
        self.basemap_raster_paths = basemap_raster_paths

    def run(self):
        """
        Export Event
        """
        try:
            # Make a copy of the QRiS riverscapes GeoPackage to the riverscapes project
            output_gpkg = os.path.join(os.path.dirname(self.output_path), 'outputs', 'qris_dce.gpkg')
            if not os.path.isdir(os.path.dirname(output_gpkg)):
                os.makedirs(os.path.dirname(output_gpkg))

            shutil.copyfile(self.db_path, output_gpkg)

            # # 1. Create Riverscapes Project output Geopackage (using QRiS schema.sql?)
            # output_gpkg = os.path.join(self.output_path, 'outputs', 'qris_dce.gpkg')
            # task = NewProject(self.iface, output_gpkg, self.output_project_name, None)
            # task.on_complete.connect(self.on_project_created)
            # result = task.run()
            # if result is False:
            #     raise task.exception

            # Delete any information that's not part of the event being exported
            with sqlite3.connect(output_gpkg) as conn:
                conn.execute("PRAGMA foreign_keys = 1")
                conn.row_factory = dict_factory
                curs = conn.cursor()

                # Get the riverscapes project type
                curs.execute('SELECT rs_project_type_code FROM methods WHERE id = ? AND rs_project_type_code is NOT NULL', [self.method_id])
                project_type = curs.fetchone()['rs_project_type_code']

                # Delete items not used by this event (that aren't caught by cascade delete)
                conn.execute('DELETE FROM events where id <> ?', [self.event_id])
                conn.execute('DELETE FROM scratch_vectors')
                conn.execute('DELETE FROM rasters WHERE id NOT IN (SELECT basemap_id FROM event_basemaps WHERE event_id = ?)', [self.event_id])
                conn.execute('DELETE FROM masks')

                # Identify all the layers that are not part of the method being exported
                curs.execute("""SELECT DISTINCT fc_name FROM layers l
                    INNER JOIN method_layers ml on l.id = ml.layer_id
                    WHERE (ml.method_id) <> ?""", [self.method_id])
                unused_fc_names = [row['fc_name'] for row in curs.fetchall()]
                [curs.execute(f'DELETE FROM {fc_name}') for fc_name in unused_fc_names]

                # Identify layers that are part of this method. They will be specified as datasets in the project
                curs.execute('SELECT l.* FROM layers l INNER JOIN method_layers ml on l.id = ml.layer_id WHERE method_id = ?', [self.method_id])
                method_layers = {row['display_name']: RSLayer(
                    row['display_name'],
                    str(row['id']),
                    'Vector',
                    row['fc_name']) for row in curs.fetchall()}

                # Basemaps files are copied as asynchronous subtasks but we need to store their new paths
                [curs.execute('UPDATE rasters SET path = ? WHERE id = ?', [path, id]) for id, path in self.basemap_raster_paths.items()]

                # Defragment database because we deleted data
                conn.commit()
                conn.execute('VACUUM')

            # Write project XML
            rs_project = RSProject(cfg, os.path.dirname(self.output_path))
            rs_project.create(self.output_project_name, project_type, [])
            realization = rs_project.add_realization(self.output_project_name, 'QRiS Data Capture Event', '0.0.0')
            inputs = rs_project.XMLBuilder.add_sub_element(realization, 'Inputs')
            outputs = rs_project.XMLBuilder.add_sub_element(realization, 'Outputs')

            # Add all the basemaps as inputs
            for id, path in self.basemap_raster_paths.items():
                rs_project.add_dataset(inputs, path, RSLayer('name', 'BASEMAP' + str(id), 'Raster'))

            # Add the copied QRiS GeoPackage that just has the Data Capture Event, with each layer as sublayer
            gpkg_layer = RSLayer('QRiS', 'OUTPUTS', 'Geopackage', rs_project.get_relative_path(output_gpkg), method_layers)
            nod_gpkg = rs_project.add_dataset(outputs, output_gpkg, gpkg_layer, 'GeoPackage')
            layers_node = rs_project.XMLBuilder.add_sub_element(nod_gpkg, 'Layers')

            for sublyr in method_layers.values():
                # sub_abs_path = os.path.join(file_path, rssublyr.rel_path)
                sub_nod = rs_project.add_dataset(layers_node, sublyr.rel_path, sublyr, sublyr.tag, rel_path=True)

            rs_project.XMLBuilder.write()

        except Exception as ex:
            self.exception = ex
            return False

        return True
