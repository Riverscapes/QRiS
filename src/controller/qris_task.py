"""
Base class from which to inherit QRiS asynchronous tasks.
This class does some of the repetitive work of degining a QgsTask.
All you need to do is inherit this class and then implement the
method Run() -> bool

When the task is complete the on_complete signal will be emitted.

Remember never to interact with the QGIS user interface in the run method..
"""

from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal


class QRiSTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_complete = pyqtSignal(bool)

    def __init__(self, iface, task_name: str, message_category: str):
        """
        iface: QGIS interface
        task_name: Display name for the task (e.g. "Copy Feature Class")
        message_category: Machine code string for grouping error messages together (e.g. QRiS_COPY_FEATURE_CLASS)
        """

        super().__init__(task_name, QgsTask.CanCancel)

        self.iface = iface
        self.message_category = message_category

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

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            self.iface.messageBar().pushMessage(f'{self.description} Complete.', level=Qgis.Info, duration=5)
            QgsMessageLog.logMessage(f'{self.description} Complete', self.message_category, Qgis.Success)
        else:
            if self.exception is None:
                self.iface.messageBar().pushMessage(f'{self.description} Error', 'See log for details.', level=Qgis.Error, duration=5)
                QgsMessageLog.logMessage(f'{self.description} was unsuccessful but without exception (probably the task was canceled by the user)', self.message_category, Qgis.Warning)
            else:
                self.iface.messageBar().pushMessage(f'{self.description} Error', 'See log for details.', level=Qgis.Error, duration=5)
                QgsMessageLog.logMessage(f'{self.description} exception: {self.exception}', self.message_category, Qgis.Critical)
                raise self.exception

        self.on_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Event Export was canceled'.format(name=self.description()), self.message_category, Qgis.Info)
        super().cancel()
