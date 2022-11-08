import os
import sqlite3

from .qris_task import QRiSTask
from .new_project import NewProject


class EventExportTask(QRiSTask):

    def __init__(self, iface, db_path: str, event_id: int, output_project_name: str, output_path: str, project_type: str):
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
        self.project_type = project_type

    def run(self):
        """
        Export Event
        """
        try:

            # 1. Create Riverscapes Project output Geopackage (using QRiS schema.sql?)
            output_gpkg = os.path.join(self.output_path, 'outputs', 'qris_dce.gpkg')
            task = NewProject(self.iface, output_gpkg, self.output_project_name, None)
            task.on_complete.connect(self.on_project_created)
            QgsApplication.taskManager().addTask(task)

            # 2. See which layers are in use by event
            with sqlite3.connect(self.db_path) as conn:
                curs = conn.cursor()
                curs.execute('SELECT * FROM event_layers WHERE event_id = ?', [self.event_id])
                layers = []

            # 3. Loop over each layer and copy features for the layers into the Riverscapes GeoPackage

            # 4. Copy any basemaps

            # 5. Write project XML

        except Exception as ex:
            self.exception = ex
            return False

        return True
