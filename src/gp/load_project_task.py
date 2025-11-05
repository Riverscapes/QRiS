from qgis.PyQt import QtWidgets
from qgis.core import QgsTask, QgsApplication, QgsMessageLog, Qgis
import traceback

from ..model.project import Project, apply_db_migrations, test_project

class LoadProjectTask(QgsTask):
    def __init__(self, db_path, callback):
        super().__init__("Load QRiS Project", QgsTask.CanCancel)
        self.db_path = db_path
        self.callback = callback
        self.qris_project = None
        self.error = None
        self.messages = []

    def run(self):
        try:
            self.setProgress(0)
            self.setDescription("Validating project database...")
            result = test_project(self.db_path)
            if not result:
                self.error = f"QRiS project database is not valid. Please check that {self.db_path} is a valid QRiS project."
                return False

            self.setProgress(33)
            self.setDescription("Applying database migrations...")
            for msg in apply_db_migrations(self.db_path):
                self.messages.append(msg)

            self.setProgress(66)
            self.setDescription("Loading project data...")
            self.qris_project = Project(self.db_path)

            self.setProgress(90)
            self.setDescription("Refreshing spatial views...")
            self.qris_project.refresh_spatial_views()

            self.setDescription("QRiS project loaded successfully.")
            self.setProgress(100)
            return True
        except Exception as ex:
            self.error = f"{ex}\n{traceback.format_exc()}"
            return False

    def finished(self, result):
        for msg in self.messages:
            QgsMessageLog.logMessage(msg, "QRiS", Qgis.Info)
        if result and self.qris_project:
            QgsMessageLog.logMessage("QRiS project loaded successfully.", "QRiS", Qgis.Info)
            self.callback(self.qris_project)
        else:
            QgsMessageLog.logMessage(f"Error loading project: {self.error}", "QRiS", Qgis.Critical)