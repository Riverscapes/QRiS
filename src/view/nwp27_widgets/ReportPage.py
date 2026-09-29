import json
import logging
import os
import tempfile
import threading

from osgeo import ogr
from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)
import requests

from .BaseWidget import BaseWidget
from .reports.ReportsWorker import ReportWorker
from .reports.RSReportsAPI import RSReportsAPI
from .WizardStatus import STEP_UNKNOWN

logger = logging.getLogger(__name__)

REPORTS = [
    {
        "name": "Project Context Report",
        "id": "project_context",
        "description": "Provides context for the project area.",
        "layer_key": "projectExtent",
        "layer_name": "sample_frame_features",
        "layer_id_field": "sample_frame_id",
        "output_folder_name": "project_context_report",
    },
    {
        "name": "Watershed Catchment Report",
        "id": "watershed_catchment",
        "description": "Provides context for the project catchment area.",
        "layer_key": "catchment",
        "layer_name": "catchments",
        "layer_id_field": "fid",
        "output_folder_name": "watershed_catchment_report",
    },
]


class ReportPage(BaseWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.polygon_path = polygon_path
        # self.setTitle("Rapid Assessment Report")

        self._report_type_id = None  # optional override
        self._worker_thread: threading.Thread | None = None
        self._current_report: dict | None = None
        self._report_buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._label = QLabel(
            "The following reports provide insights into your project area. "
            "Click the Generate button to initiate a report. "
            "A web browser will open where you need to sign in to the Riverscapes Reporting platform. "
            "Reports take several minutes to generate, so please be patient.\n\n"
            "Once a report is complete, it will open in a web browser. "
            "Completed reports, including all the associated files, are automatically downloaded"
            "and placed in the NWP27 package folder. Click the folder icon to browse them."
        )
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        layout.addSpacing(20)

        for report in REPORTS:
            name = report["name"]
            description = report["description"]
            report_id = report["id"]

            h_layout = QHBoxLayout()
            layout.addLayout(h_layout)

            name_label = QLabel(name)
            h_layout.addWidget(name_label)

            description_label = QLabel(description)
            description_label.setWordWrap(True)
            h_layout.addWidget(description_label)

            generate_button = QPushButton("Generate")
            generate_button.setMaximumWidth(75)
            generate_button.setToolTip(f"Generate the {name}")
            generate_button.clicked.connect(lambda _, report_id=report_id: self.generate_report_by_id(report_id))
            h_layout.addWidget(generate_button)

            open_button = QPushButton()
            open_button.setMaximumWidth(self.BUTTON_WIDTH)
            open_button.setToolTip(f"Open the {name}")
            open_button.setIcon(QIcon(":plugins/qris_toolbar/open"))
            open_button.clicked.connect(lambda _, report_id=report_id: self.open_report_by_id(report_id))
            h_layout.addWidget(open_button)

            browse_button = QPushButton()
            browse_button.setMaximumWidth(self.BUTTON_WIDTH)
            browse_button.setIcon(QIcon(":plugins/qris_toolbar/folder"))
            browse_button.setToolTip(f"Browse the {name} folder")
            browse_button.clicked.connect(lambda _, report_id=report_id: self.browse_report_by_id(report_id))
            h_layout.addWidget(browse_button)

            self._report_buttons[f"browse_{report_id}"] = browse_button

            self._report_buttons[report_id] = generate_button
            self._report_buttons[f"open_{report_id}"] = open_button

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        layout.addSpacing(20)
        self.report_platform_label = QLabel("Completed reports are also retained on the Riverscapes Reports platform for 7 days, so be sure to verify the downloaded files before they expire or you will need to generate a new copy.")
        self.report_platform_label.setWordWrap(True)
        layout.addWidget(self.report_platform_label)

        reports_platform_button = QPushButton("Riverscapes Reports Platform")
        reports_platform_button.setToolTip("Open the Riverscapes Reports platform")
        reports_platform_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        reports_platform_button.clicked.connect(lambda _: QDesktopServices.openUrl(QUrl("https://reports.riverscapes.net")))
        layout.addWidget(reports_platform_button)

        layout.addStretch()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def get_status(self) -> int:

        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def generate_report_by_id(self, report_id: str):
        report = next((r for r in REPORTS if r["id"] == report_id), None)
        if report is None:
            logger.error("Unknown report id: %s", report_id)
            return

        layer_id = self.get_layer_id(report["layer_key"])
        if layer_id is None:
            QMessageBox.warning(self, "Missing Layer", f"You must specify a {report['name'].lower()} polygon on the Locations step before generating this report.")
            return

        polygon = self.load_polygon_from_db(report["layer_name"], report["layer_id_field"], layer_id)
        if polygon is None:
            QMessageBox.warning(self, "Missing Polygon", f"Could not find the polygon for the {report['name'].lower()}. Check your selections on the Locations step.")
            return

        self.generate_report(report, polygon)

    def open_report_by_id(self, report_id: str):
        report = next((r for r in REPORTS if r["id"] == report_id), None)
        if report is None:
            logger.error("Unknown report id: %s", report_id)
            return

        report_html_path = os.path.join(self.get_package_folder(), report["output_folder_name"], "report.html")
        if not os.path.exists(report_html_path):
            QMessageBox.information(self, "Report Not Found", f"The {report['name']} has not been generated yet. Click Generate first.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(report_html_path))

    def browse_report_by_id(self, report_id: str):
        report = next((r for r in REPORTS if r["id"] == report_id), None)
        if report is None:
            logger.error("Unknown report id: %s", report_id)
            return

        output_folder = os.path.join(self.get_package_folder(), report["output_folder_name"])
        if not os.path.isdir(output_folder):
            QMessageBox.information(self, "Report Not Found", f"The {report['name']} has not been generated yet. Click Generate first.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(output_folder))

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

    def generate_report(self, report: dict, polygon: str):
        if self._worker_thread and self._worker_thread.is_alive():
            return  # already running

        self._current_report = report

        for button in self._report_buttons.values():
            button.setEnabled(False)
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
        self.on_text_changed()

        creator_id = report.get("_creator_id")
        report_id = report["id"]
        urls = RSReportsAPI.get_report_view_urls(creator_id, report_id)
        zip_url = urls.get("zip")
        output_folder = os.path.join(self.get_package_folder(), self._current_report.get("output_folder_name", "report"))
        os.makedirs(output_folder, exist_ok=True)
        local_path = os.path.join(output_folder, "report.zip")

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

        self._reset_ui()

        # msg_box = QMessageBox(self)
        # msg_box.setWindowTitle("Report Generated")
        # msg_box.setText(
        #     f"Your report has been generated successfully!\n\n"
        #     f"Status: {report['status']}\n"
        #     f"Progress: {report.get('progress', 100)}%\n\n"
        #     f"View your report:\n{urls['html']}\n\n"
        #     f"PDF download:\n{urls['pdf']}\n\n"
        #     f"Would you like to open the report in your browser?"
        # )
        # msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        # if msg_box.exec() == QMessageBox.StandardButton.Yes:
        #     QDesktopServices.openUrl(QUrl(urls["html"]))

    def _on_worker_error(self, error_msg: str):
        QMessageBox.critical(self, "Report Generation Failed", f"An error occurred while generating the report:\n\n{error_msg}")
        self._reset_ui()

    def _reset_ui(self):
        for button in self._report_buttons.values():
            button.setEnabled(True)
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
