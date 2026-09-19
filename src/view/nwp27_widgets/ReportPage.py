import logging
import threading

from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .DBCon import DBCon
from .reports.ReportsWorker import ReportWorker
from .reports.RSReportsAPI import RSReportsAPI
from .WizardStatus import STEP_UNKNOWN

logger = logging.getLogger(__name__)


class ReportPage(BaseWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.polygon_path = polygon_path
        # self.setTitle("Rapid Assessment Report")

        self._report_type_id = None  # optional override
        self._worker_thread: threading.Thread | None = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._label = QLabel(
            "The Rapid Assessment Report brings together disparate and relevant "
            "information that can help you complete your NWP 27 permit application.\n\n"
            "Clicking the button below will launch a web browser where you need to sign "
            "in to the Riverscapes Reporting platform. Once signed in, your project "
            "extent will automatically be uploaded and a new Rapid Assessment Report "
            "will be generated for you. The report takes a few minutes to generate, "
            "so please be patient. Once the report is generated, you will be able to "
            "download it as a PDF and upload it to your NWP 27 permit application.\n\n"
            "Existing reports are available in the Riverscapes Reporting platform, so "
            "if you have already generated a report for this project, you can download "
            "it from there instead of generating a new one.\n\n"
            "Reports are retained on the reporting platform for 7 days, so be sure to "
            "download it before it expires or you will need to generate a new one."
        )
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        self._button = QPushButton("Generate Project Context Report")
        self._button.clicked.connect(self.generate_project_context_report)
        layout.addWidget(self._button)

        self._button = QPushButton("Generate Watershed Catchment Report")
        self._button.clicked.connect(self.generate_watershed_catchment_report)
        layout.addWidget(self._button)

        layout.addStretch()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def get_status(self) -> int:
        if self._button.text() == "Report Complete":
            return STEP_UNKNOWN
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def generate_project_context_report(self):

        polygon = self.load_polygon_from_db("project_context_layer", "project_context_polygon_id")

        if polygon is None:
            QMessageBox.warning(self, "Missing Project Extent Polygon", "You must specify a project extent polygon on the Locations step before generating this report.")
            return

        self.generate_report("Project Context Report", polygon)

    def generate_watershed_catchment_report(self):

        polygon = self.load_polygon_from_db("watershed_catchment_layer", "watershed_catchment_polygon_id")
        if polygon is None:
            QMessageBox.warning(self, "Missing Catchment Polygon", "You must generate a QRiS pour point analysis and then specify the catchment polygon on the Locations step before generating this report.")
            return

        self.generate_report("Watershed Catchment Report", polygon)

    def load_polygon_from_db(self, layer_name: str, polygon_id: str) -> str:

        with DBCon.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT geom FROM {layer_name} WHERE id = ?", (polygon_id,))
            result = cursor.fetchone()
            if result:
                return result["geom"]
            return None

    def generate_report(self, title: str, polygon: str):
        if self._worker_thread and self._worker_thread.is_alive():
            return  # already running

        self._button.setEnabled(False)
        self._button.setText("Generating...")
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setVisible(True)
        self._status_label.setText("Starting...")

        if not self.polygon_path:
            QMessageBox.warning(self, "Missing Polygon", "No project polygon file was provided. Please go back to the Location page and select an extent.")
            self._reset_ui()
            return

        worker = ReportWorker(self.polygon_path, self._report_type_id)
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)

        thread = threading.Thread(target=worker.run, daemon=True)
        self._worker_thread = thread
        thread.start()

    def _on_worker_progress(self, status: str, progress_pct: int, message: str):
        self._progress_bar.setValue(progress_pct)
        self._status_label.setText(f"[{status}] {message}")

    def _on_worker_finished(self, report: dict):
        self._progress_bar.setValue(100)
        self._status_label.setText("Report generated successfully!")
        self._button.setText("Report Complete")
        self._button.setEnabled(False)
        self.on_text_changed()

        creator_id = report.get("_creator_id")
        report_id = report["id"]
        urls = RSReportsAPI.get_report_view_urls(creator_id, report_id)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Report Generated")
        msg_box.setText(
            f"Your report has been generated successfully!\n\n"
            f"Status: {report['status']}\n"
            f"Progress: {report.get('progress', 100)}%\n\n"
            f"View your report:\n{urls['view']}\n\n"
            f"PDF download:\n{urls['pdf']}\n\n"
            f"Would you like to open the report in your browser?"
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(urls["view"]))

    def _on_worker_error(self, error_msg: str):
        QMessageBox.critical(self, "Report Generation Failed", f"An error occurred while generating the report:\n\n{error_msg}")
        self._reset_ui()

    def _reset_ui(self):
        self._button.setEnabled(True)
        self._button.setText("Generate Report")
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(False)
