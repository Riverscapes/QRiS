import json
import logging
import os
import tempfile
import threading

from osgeo import ogr
from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)
import requests

from .BaseWidget import BaseWidget
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

        self.project_report_button = QPushButton("Generate Project Context Report")
        self.project_report_button.clicked.connect(self.generate_project_context_report)
        layout.addWidget(self.project_report_button)

        self.watershed_report_button = QPushButton("Generate Watershed Catchment Report")
        self.watershed_report_button.clicked.connect(self.generate_watershed_catchment_report)
        layout.addWidget(self.watershed_report_button)

        layout.addStretch()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def get_status(self) -> int:
        if self.project_report_button.text() == "Report Complete":
            return STEP_UNKNOWN
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def generate_project_context_report(self):

        project_extent_id = self.get_layer_id("projectExtent")
        if project_extent_id is None:
            QMessageBox.warning(self, "Missing Project Extent", "You must specify a project extent polygon on the Locations step before generating this report.")
            return

        # projectExtent stores a sample_frames.id; the geometry lives in sample_frame_features
        polygon = self.load_polygon_from_db("sample_frame_features", "sample_frame_id", project_extent_id)

        if polygon is None:
            QMessageBox.warning(self, "Missing Project Extent Polygon", "You must specify a project extent polygon on the Locations step before generating this report.")
            return

        self.generate_report("Project Context Report", polygon)

    def generate_watershed_catchment_report(self):

        catchment_id = self.get_layer_id("catchment")
        if catchment_id is None:
            QMessageBox.warning(self, "Missing Catchment", "You must specify a catchment polygon on the Locations step before generating this report.")
            return

        # catchment stores a catchments.fid
        polygon = self.load_polygon_from_db("catchments", "fid", catchment_id)
        if polygon is None:
            QMessageBox.warning(self, "Missing Catchment Polygon", "You must generate a QRiS pour point analysis and then specify the catchment polygon on the Locations step before generating this report.")
            return

        self.generate_report("Watershed Catchment Report", polygon)

    def load_polygon_from_db(self, layer_name: str, id_column: str, polygon_id) -> str | None:
        """Load a feature geometry from the project GPKG and return it as a GeoJSON geometry string.

        The geom column is stored in OGR binary format, so we read it through OGR
        (same pattern as src/gp/analysis_metrics.py) and serialize with ExportToJson().
        """
        if polygon_id is None:
            return None
        ds: ogr.DataSource = ogr.Open(self.db_path)
        if ds is None:
            logger.error("Could not open GPKG: %s", self.db_path)
            return None
        layer: ogr.Layer = ds.GetLayerByName(layer_name)
        if layer is None:
            logger.error("Layer %s not found in %s", layer_name, self.db_path)
            return None
        layer.SetAttributeFilter(f"{id_column} = {polygon_id}")
        feature: ogr.Feature = layer.GetNextFeature()
        if feature is None or feature.GetGeometryRef() is None:
            return None
        geom: ogr.Geometry = feature.GetGeometryRef().Clone()
        return geom.ExportToJson()

    def generate_report(self, title: str, polygon: str):
        if self._worker_thread and self._worker_thread.is_alive():
            return  # already running

        self.project_report_button.setEnabled(False)
        self.watershed_report_button.setEnabled(False)
        # self.project_report_button.setText("Generating...")
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setVisible(True)
        self._status_label.setText("Starting...")

        # Write the GeoJSON geometry to a temp file for the worker to upload
        polygon_path = self._write_polygon_to_temp_file(polygon)
        if polygon_path is None:
            QMessageBox.warning(self, "Failed to Write Temporary Polygon File", "Could not write the project polygon to a temporary file.")
            self._reset_ui()
            return

        worker = ReportWorker(polygon_path, self._report_type_id)
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)

        thread = threading.Thread(target=worker.run, daemon=True)
        self._worker_thread = thread
        thread.start()

    def _write_polygon_to_temp_file(self, polygon: str) -> str | None:
        """Write a GeoJSON geometry string to a temp FeatureCollection file and return its path."""
        try:
            feature_collection = {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "properties": {}, "geometry": json.loads(polygon)}],
            }
            fd, path = tempfile.mkstemp(suffix=".geojson")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(feature_collection, f)
            return path
        except Exception:
            logger.exception("Failed to write polygon to temp file")
            return None

    def _on_worker_progress(self, status: str, progress_pct: int, message: str):
        self._progress_bar.setValue(progress_pct)
        self._status_label.setText(f"[{status}] {message}")

    def _on_worker_finished(self, report: dict):
        self._progress_bar.setValue(100)
        self._status_label.setText("Report generated successfully!")
        self.project_report_button.setText("Report Complete")
        self.project_report_button.setEnabled(False)
        self.on_text_changed()

        creator_id = report.get("_creator_id")
        report_id = report["id"]
        urls = RSReportsAPI.get_report_view_urls(creator_id, report_id)
        zip_url = urls.get("zip")
        local_path = os.path.join(self.get_package_folder(), "report.zip")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if zip_url:
            # Download the zip file to the local path
            try:
                response = requests.get(zip_url)
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(response.content)

                # Unzip the zip file to the same directory and open the report.html file if it exists
                import zipfile

                with zipfile.ZipFile(local_path, "r") as zip_ref:
                    zip_ref.extractall(os.path.dirname(local_path))
                    report_html_path = os.path.join(os.path.dirname(local_path), "report.html")
                    if os.path.exists(report_html_path):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(report_html_path))

            except Exception:
                logger.exception("Failed to download report zip file")
                QMessageBox.critical(self, "Download Failed", "Failed to download the report zip file.")
                return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Report Generated")
        msg_box.setText(
            f"Your report has been generated successfully!\n\n"
            f"Status: {report['status']}\n"
            f"Progress: {report.get('progress', 100)}%\n\n"
            f"View your report:\n{urls['html']}\n\n"
            f"PDF download:\n{urls['pdf']}\n\n"
            f"Would you like to open the report in your browser?"
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(urls["html"]))

    def _on_worker_error(self, error_msg: str):
        QMessageBox.critical(self, "Report Generation Failed", f"An error occurred while generating the report:\n\n{error_msg}")
        self._reset_ui()

    def _reset_ui(self):
        self.project_report_button.setEnabled(True)
        self.watershed_report_button.setEnabled(True)
        # self.project_report_button.setText("Generate Report")
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(False)

    def get_layer_id(self, layer_key: str) -> int | None:
        """
        This method retrieves the layer ID that the user picked on the LocationsPage.

        Pass in "projectExtent" or "catchment" depending which report you want to generate.
        """

        data = self.load_data("locations")
        if data is not None:
            layer_id = data.get(layer_key)
            return layer_id

        return None
