from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal


MESSAGE_CATEGORY = 'QRiS_EventExportTask'


class EventExportTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_complete = pyqtSignal(bool)

    def __init__(self, iface, db_path: str, event_id: int, output_path: str):
        super().__init__(f'Export Event Task', QgsTask.CanCancel)

        self.iface = iface
        self.db_path = db_path
        self.event_id = event_id
        self.output_path = output_path

    def run(self):
        """
        Export Event
        """
        try:
            self.perform_export()
        except Exception as ex:
            self.exception = ex
            return False

        return True

    def perform_export(self):
        print('Not implemented')

        # 1. Create Riverscapes Project output Geopackage (using QRiS schema.sql?)

        # 2. See which layers are in use by event
        # SELECT * FROM event_layers WHERE event_id = ?

        # 3. Loop over each layer and copy features for the layers into the Riverscapes GeoPackage

        # 4. Copy any basemaps

        # 5. Write project XML

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            self.iface.messageBar().pushMessage('Event Export Complete.', self.output_path, level=Qgis.Info, duration=5)
            QgsMessageLog.logMessage('Event Export Complete', MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                self.iface.messageBar().pushMessage('Event Export Error', 'See log for details.', level=Qgis.Error, duration=5)
                QgsMessageLog.logMessage(
                    'Event Export was unsuccessful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                self.iface.messageBar().pushMessage('Event Export Error', 'See log for details.', level=Qgis.Error, duration=5)
                QgsMessageLog.logMessage(f'Event Export exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.on_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Event Export was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
